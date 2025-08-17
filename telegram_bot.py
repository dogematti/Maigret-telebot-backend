import logging
import os
import asyncio
from typing import Dict

from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import Application, CommandHandler, ContextTypes

# Maigret imports
from maigret.sites import MaigretDatabase, MaigretSite
from maigret.checking import maigret
from maigret.notify import QueryNotifyPrint
from maigret.settings import Settings
from maigret.types import QueryResultWrapper, QueryOptions
from maigret.result import MaigretCheckStatus

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Replace with your actual bot token from BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1)

# Global Maigret instances
maigret_db: MaigretDatabase = None
maigret_settings: Settings = None

MAX_MESSAGE_LENGTH = 4000

async def send_long_message(update: Update, text: str):
    if len(text) <= MAX_MESSAGE_LENGTH:
        try:
            await asyncio.sleep(0.1) # Add a small delay
            await update.message.reply_text(text)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            await update.message.reply_text(text)
    else:
        # Split the message into chunks
        chunks = []
        current_chunk = ""
        for line in text.splitlines(True): # Keep newlines
            if len(current_chunk) + len(line) > MAX_MESSAGE_LENGTH:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line
        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            try:
                await asyncio.sleep(0.1) # Add a small delay
                await update.message.reply_text(chunk)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                await update.message.reply_text(chunk)

class QueryNotifyTelegram(QueryNotifyPrint):
    """Custom QueryNotify class to send updates to Telegram."""
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_obj = update
        self.context = context
        self.message_id = None

    def start(self, username: str, id_type: str):
        # asyncio.create_task(self.send_message(f"Starting search for {username} ({id_type})..."))
        pass

    

    def finish(self):
        # asyncio.create_task(self.send_message("Search finished."))
        pass

    async def send_message(self, text: str):
        message = await self._update_obj.message.reply_text(text)
        self.message_id = message.message_id

    async def edit_or_send_message(self, text: str):
        if self.message_id:
            try:
                await self.context.bot.edit_message_text(
                    chat_id=self._update_obj.effective_chat.id,
                    message_id=self.message_id,
                    text=text
                )
            except Exception:
                # If message cannot be edited (e.g., too old), send a new one
                await self.send_message(text)
        else:
            await self.send_message(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text( # Changed to reply_text
        f"""Hi {user.full_name}!
I'm a Maigret bot. Send me a username with /search <username> to find information.""",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Use /search <username> to perform a Maigret search.\n"
        "Example: /search johndoe"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perform a Maigret search for the given username."""
    if not context.args:
        await update.message.reply_text("Please provide a username. Example: /search johndoe")
        return

    username = context.args[0]
    await update.message.reply_text(f"Searching for {username}...")

    global maigret_db, maigret_settings
    if maigret_db is None or maigret_settings is None:
        await update.message.reply_text("Initializing Maigret database and settings...")
        maigret_settings = Settings()
        settings_loaded, err = maigret_settings.load()
        if not settings_loaded:
            await update.message.reply_text(f"Failed to load settings: {err}")
            return

        db_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "maigret", "resources", "data.json")
        maigret_db = MaigretDatabase().load_from_path(db_file)
        await update.message.reply_text("Maigret initialization complete.")

    query_notify = QueryNotifyTelegram(update, context)

    # Prepare site_dict - for simplicity, load all sites
    site_dict: Dict[str, MaigretSite] = maigret_db.ranked_sites_dict(
        top=maigret_settings.top_sites_count,
        tags=[],
        names=[],
        disabled=maigret_settings.scan_disabled_sites,
        id_type="username", # Assuming username search for now
    )

    if not site_dict:
        await update.message.reply_text("No sites available for search with current settings.")
        return

    try:
        results = await maigret(
            username=username,
            site_dict=site_dict,
            logger=logger,
            query_notify=query_notify,
            timeout=maigret_settings.timeout,
            is_parsing_enabled=maigret_settings.info_extracting,
            id_type="username",
            debug=False,
            forced=False,
            max_connections=maigret_settings.max_connections,
            no_progressbar=True, # Disable progress bar for bot
            cookies=None,
            retries=maigret_settings.retries_count,
            check_domains=maigret_settings.domain_search,
        )

        found_sites = [
            f"✅ {site_name}" for site_name, result_wrapper in results.items()
            if result_wrapper.get("status") and result_wrapper["status"].status == MaigretCheckStatus.CLAIMED
        ]
        not_found_sites = [
            f"❌ {site_name}" for site_name, result_wrapper in results.items()
            if result_wrapper.get("status") and result_wrapper["status"].status == MaigretCheckStatus.AVAILABLE
        ]

        response_message = f"Search results for {username}:\n\n"
        if found_sites:
            response_message += "Found on:\n" + "\n".join(found_sites) + "\n\n"
        if not_found_sites:
            response_message += "Not found on:\n" + "\n".join(not_found_sites) + "\n\n"
        if not found_sites and not not_found_sites:
            response_message += "No results found or an error occurred during search."

        await send_long_message(update, response_message)

    except Exception as e:
        logger.error(f"Error during Maigret search: {e}", exc_info=True)
        await update.message.reply_text(f"An error occurred during the search: {e}")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(60).build()

    # on different commands - add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()