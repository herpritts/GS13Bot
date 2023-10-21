"""
helpers.py

This module contains the `Helper` class, which provides the following functionality:

- `generate_username`: Generates a username by combining a prefix with a 
  random noun from a JSON file.
- `generate_update_message_text`: Generates a message text based on whether 
  a job has been posted or not.
- `error_handler`: Handles any errors that occur during an update by logging 
  the error message.

The `Helper` class uses a JSON file of structured random nouns to generate usernames.
The file path can be specified during the initialization of the class. The class also keeps track of
the time when the first job was found.

The module uses the `logging` library to log information and error messages.
"""
import json
import logging
import random
import sys
import time
from telegram import Update
from telegram.ext import CallbackContext

class Helper:
    """
    This Helper class provides utility functions for generating usernames and update messages.
    It also handles errors that occur during an update.
    """
    def __init__(self, nouns_file='./structured_random_nouns.json'):
        self.nouns_file = nouns_file
        self.initial_job_found_time = None

    def generate_username(self, prefix='Black') -> str:
        """
        Generate a username by combining a prefix with a random noun from a JSON file.
        
        :param prefix: The prefix to use for the username. Defaults to 'Black'.
        :return: The generated username.
        """
        try:
            with open(self.nouns_file, 'r', encoding='UTF-8') as file:
                data = json.load(file)
                random_nouns = data['words']
        except FileNotFoundError:
            logging.error("%s not found.", self.nouns_file)
            raise
        except json.JSONDecodeError:
            logging.error("%s has an invalid format.", self.nouns_file)
            raise

        username = f'{prefix} {random.choice(random_nouns)}'
        logging.info("Generated username: %s", username)
        return username

    def generate_update_message_text(
        self,
        is_job_posted: bool,
        timestamp_format='%Y-%m-%d %H:%M:%S'
    ) -> str:
        """
        Generate a message text based on whether a job has been posted or not.
        
        :param context: The context of the update.
        :param is_job_posted: Whether a job has been posted or not.
        :param timestamp_format: The format for the timestamp. Defaults to 
        '%Y-%m-%d %H:%M:%S'.
        :return: The generated message text.
        """
        timestamp = time.strftime(timestamp_format, time.localtime())

        if is_job_posted:
            logging.info("Job found!")
            if self.initial_job_found_time is None:
                self.initial_job_found_time = timestamp
            return (
                f"Job found! Initially found at {self.initial_job_found_time}. "
                f"Last verified at {timestamp}.\n/deactivate"
            )
        else:
            logging.info("Job not found.")
            return f"Not yet... Last checked at {timestamp}"

    @staticmethod
    def error_handler(update: Update, context: CallbackContext) -> None:
        """
        Handle any errors that occur during an update.
        
        :param update: The update that caused the error.
        :param context: The context of the update.
        """
        logging.error("Update %s caused error: %s", update, context.error)

    @staticmethod
    def signal_handler():
        """
        Handle any signals received by the bot.
        
        :param sig: The signal received.
        :param frame: The current stack frame.
        """
        logging.info("Signal received, stopping the bot...")
        sys.exit(0)
