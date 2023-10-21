# main.py

# Standard library imports
import json
import logging
import signal

# Third-party imports
from telegram import Update
from telegram.ext import Application

# Local application imports
from utils import fetch_environment_variables, init_logging
from command_handlers import CommandHandlers
from user_data_manager import UserDataManager
from update_manager import UpdateManager

# Initialize logging
logger = init_logging()

# Constants
DEFAULT_USERNAME = "Black Cat"
REFRESH_INTERVAL = 60

def main(user_data_file='./data/user_data.json') -> None:
    """Runs the Telegram bot application."""
    try:
        # Load user data from JSON file
        try:
            data_manager = UserDataManager(user_data_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error("Failed to load user data: %s", e)
            raise

        # Get the bot token from environment variables
        token = fetch_environment_variables()["TELEGRAM_BOT_TOKEN"]
 
        application = Application.builder().token(token).build()

        command_handlers = CommandHandlers(data_manager)
        command_handlers.setup_command_handlers(application)

        update_manager = UpdateManager(application, data_manager)

        # Setup command handlers
        command_handlers.setup_command_handlers(application)

        # Schedule sending updates every REFRESH_INTERVAL seconds
        application.job_queue.run_repeating(
            update_manager.get_update,
            interval=REFRESH_INTERVAL,
            first=0
        )

        # Register the signal handler
        signal.signal(signal.SIGINT, application.stop)

        logging.info("Bot started. Press Ctrl+C to exit.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as error:
        logging.error("An error occurred while initializing the bot: %s", error)
        raise

if __name__ == "__main__":
    main()
