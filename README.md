# Maigret Telegram Bot

This is a Telegram bot designed to interact with the Maigret OSINT tool, allowing users to perform OSINT queries directly from Telegram. This project leverages Poetry for efficient dependency management and project execution.

## Features

*   (Add specific features here, e.g., "Search for usernames across various platforms")
*   (Add more features as they are implemented)

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.9+**: Download the latest version from [python.org](https://www.python.org/downloads/).
*   **Poetry**: If you don't have Poetry installed, follow the official installation guide: [Poetry Installation](https://python-poetry.org/docs/#installation).

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/maigret-tele-bot.git
    cd maigret-tele-bot
    ```

2.  **Install dependencies using Poetry:**

    ```bash
    poetry install
    ```

## Configuration

Before running the bot, you need to set up your Telegram Bot Token. It is highly recommended to use environment variables for sensitive information.

1.  **Obtain a Bot Token:** Talk to BotFather on Telegram to create a new bot and get your API token.
2.  **Set Environment Variable:**

    ```bash
    export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    ```

    Replace `YOUR_TELEGRAM_BOT_TOKEN` with the actual token you received from BotFather.

## Usage

To start the Telegram bot, ensure your environment variables are set, then execute the main script using Poetry:

```bash
poetry run python telegram_bot.py
```

The bot should now be running and accessible via Telegram.

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. (Note: A LICENSE file should be created separately if not already present.)
