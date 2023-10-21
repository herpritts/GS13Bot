"""
This module contains the UpdateManager class which is responsible for managing
updates within the application.

The UpdateManager class provides methods to send and get updates. It interacts with the 
Telegram API to send messages to the user based on the status of job postings. It also 
manages user data through the data_manager attribute.

Classes:
    UpdateManager: Manages updates for the application, including sending and getting updates.

Functions:
    init_logging(): Initializes logging for the module.
    check_for_job_posting(): Checks for new job postings.

Imports:
    logging: Standard library module for event logging.
    aiohttp: Asynchronous HTTP client/server for asyncio and Python.
    telegram.Bot: Class to interact with the Telegram Bot API.
    telegram.error.TelegramError: Base class for all exceptions in the telegram package.
    user_data_manager.UserDataManager: Class to manage user data.
    utils.init_logging: Function to initialize logging.
    helpers.Helper: Class providing helper methods.
    job_search.check_for_job_posting: Function to check for new job postings.
"""

import logging
import aiohttp
from telegram import Bot
from telegram.error import TelegramError
from user_data_manager import UserDataManager

from utils import init_logging
from helpers import Helper
from job_search import check_for_job_posting
from exceptions import JobPostingError, NetworkError

# Initialize logging
logger = init_logging()

class UpdateManager:
    """
    This class is responsible for managing updates within the application.

    The UpdateManager class provides methods to send and get updates. It interacts with the 
    Telegram API to send messages to the user based on the status of job postings. It also 
    manages user data through the data_manager attribute.

    Attributes:
        application: An instance of the application that the UpdateManager is part of.
        data_manager (UserDataManager): An instance of UserDataManager to manage user data.

    Methods:
        send_update(message_text: str): Sends the generated update message to the user
            and stores the message ID.
        get_update(): Gets updates to send to the user.
    """
    def __init__(self, application, data_manager: UserDataManager):
        self.application = application
        self.data_manager = data_manager

    async def send_update(self, message_text: str) -> None:
        """
        Sends the generated update message to the user and stores the message ID.

        Parameters:
            message_text (str): The message text to send.

        Returns:
            None
        """
        if not isinstance(self.application.bot, Bot):
            logging.error("Unexpected type for application.bot: %s", type(self.application.bot))
            return

        job_found = "Job found!" in message_text  # Check if the job has been found

        for user_id, user_data in self.data_manager.user_data_dict.items():
            chat_id = user_data.get('chat_id', None)
            status_message_id = user_data.get('status_message_id', None)
            active = user_data.get('active', False)

            # Check if chat_id exists
            if chat_id is None:
                logging.warning("Chat ID not found for user %s. Skipping.", user_id)
                continue

            # Check if the user has activated updates
            if not active:
                logging.info("User %s has not activated updates. Skipping.", user_id)
                continue

            try:
                # If the job has been found, send the message
                if job_found:
                    new_message = await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=message_text
                    )
                    logging.info(
                        "Successfully sent status message for chat_id %d: %s",
                        chat_id, new_message.text
                    )

                # If the job has not been found and there is an existing status message,
                # edit the message
                elif status_message_id is not None:
                    edited_message = await self.application.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text=message_text
                    )
                    logging.info(
                        "Successfully edited status message for chat_id %d, message_id %d: %s",
                        chat_id, status_message_id, edited_message.text
                    )

                # If the job has not been found and there is no existing status message,
                # send a new message
                else:
                    new_message = await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=message_text
                    )

                    user_data = self.data_manager.get_user_data(user_id)
                    user_data['status_message_id'] = new_message.message_id
                    self.data_manager.update_user_data(user_id, user_data)

                    logging.info(
                        "Successfully sent new status message for chat_id %d: %s",
                        chat_id, new_message.text
                    )
            except (TelegramError, aiohttp.ClientError) as error:
                logging.error("An error occurred while sending status message: %s", error)
                return

    async def get_update(self) -> None:
        """
        Gets updates to send to the user. Utilizes the UpdateManager's application attribute 
        to interact with the Telegram API and send messages to the user based on the status 
        of job postings.

        Returns:
            None
        """
        try:
            status = bool(check_for_job_posting())
        except JobPostingError as error:
            logging.error("An error occurred while checking for job posting: %s", error)
            return
        except NetworkError as error:
            logging.error("A network error occurred while checking for job posting: %s", error)
            return

        message_text = Helper.generate_update_message_text(self.application, is_job_posted=status)
        await self.send_update(message_text)
