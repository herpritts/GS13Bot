# Standard library imports
import json
import logging
import random
import re
import signal
import sys
import threading
import time

# Third-party imports
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher
from telegram.ext import ConversationHandler, MessageHandler, Filters

# Local application imports
from job_search import check_for_job_posting
from utils import fetch_environment_variables
from utils import load_from_json, save_to_json
from utils import init_logging

# Initialize logging
init_logging()

# Constants
DEFAULT_USERNAME = "Black Cat"
REFRESH_INTERVAL = 60

# Establish that the job is not posted
is_job_posted = False
initial_job_found_time = None

# Load user data from JSON file
try:
    user_data_dict = load_from_json('user_data.json')
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.error("Failed to load user data: %s", e)

def start_send_updates_thread(dispatcher: Dispatcher, interval: int = REFRESH_INTERVAL) -> None:
    """
    Sends updates to the user every interval seconds.

    Parameters:
        dispatcher (telegram.ext.Dispatcher): The dispatcher object for the bot.
        interval (int): The time interval for sending updates.

    Returns:
        None
    """
    try:
        get_updates(dispatcher)
    except (ConnectionError, ValueError) as error:
        logging.error("An error occurred while sending updates: %s", error)

    # Start a new thread to send updates after the specified interval
    threading.Timer(interval, start_send_updates_thread, args=[dispatcher]).start()

def get_updates(context: CallbackContext) -> None:
    """
    Gets updates to send to the user.

    Parameters:
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        None
    """
    try:
        status = bool(check_for_job_posting())
    except Exception as error:
        logging.error("An error occurred while checking for job posting: %s", error)
        return

    message_text = generate_update_message_text(context, is_job_posted=status)

    send_update(context, message_text)

def generate_update_message_text(context: CallbackContext, is_job_posted: bool) -> str:
    """
    Updates the message text based on the value of is_job_posted.

    Parameters:
        context (telegram.ext.CallbackContext): The context object for the callback.
        is_job_posted (bool): The condition to check.

    Returns:
        str: A string containing the updated message text.
    """
    global initial_job_found_time

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    if is_job_posted:
        logging.info("Job found!")
        if initial_job_found_time is None:
            initial_job_found_time = timestamp
        return f"Job found! Initially found at {initial_job_found_time}. Last verified at {timestamp}.\n/deactivate"
    else:
        logging.info("Job not found.")
        return f"Not yet... Last checked at {timestamp}"

def send_update(context: CallbackContext, message_text: str) -> None:
    """
    Sends the generated update message to the user and stores the message ID.

    Parameters:
        context (telegram.ext.CallbackContext): The context object for the callback.
        message_text (str): The message text to send.

    Returns:
        None
    """
    job_found = "Job found!" in message_text  # Check if the job has been found

    for user_id, user_data in user_data_dict.items():
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
                context.bot.send_message(
                    chat_id = chat_id,
                    text = message_text
                )

            # If the job has not been found and there is an existing status message, edit the message
            elif status_message_id is not None:
                edited_message = context.bot.edit_message_text(
                    chat_id = chat_id,
                    message_id = status_message_id,
                    text = message_text
                )
                logging.info(
                    "Successfully edited status message for chat_id %d, message_id %d: %s",
                    chat_id, status_message_id, edited_message.text
                )

            # If the job has not been found and there is no existing status message, send a new message
            else:
                new_message = context.bot.send_message(
                    chat_id = chat_id,
                    text = message_text
                )
                user_data_dict[user_id]['status_message_id'] = new_message.message_id
                save_to_json(user_data_dict, 'user_data.json')
                logging.info(
                    "Sent new status for chat_id %d, message_id %d: %s",
                    new_message.message_id, chat_id, new_message.text
                )

        except Exception as error:
            logging.error(
                "Failed to send/edit message for chat_id %d: %s",
                chat_id, error
            )

def repost(update: Update, context: CallbackContext) -> None:
    """
    Reposts the latest status message.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        None
    """
    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return

    chat_id = user_data_dict[user_id]['chat_id']
    status_message_id = user_data_dict[user_id]['status_message_id']

    try:
        if status_message_id is None:
            update.message.reply_text("No status message to repost.")
            return

        # Fetch the current status message text
        new_status_message_id = context.bot.copyMessage(
            chat_id = chat_id,
            from_chat_id = chat_id,
            message_id = status_message_id
        ).message_id

        # Update the status message ID for this user
        user_data_dict[user_id]['status_message_id'] = new_status_message_id

        logging.info(
            "Reposted status message. New message_id %d for chat_id %d",
            new_status_message_id, chat_id
        )

        # Save the updated user_data_dict to a JSON file
        save_to_json(user_data_dict, 'user_data.json')

    except Exception as error:
        logging.error(
            "Failed to repost status message for chat_id %d: %s",
            chat_id, error
        )

def start(update: Update, context: CallbackContext) -> None:
    """
    Handles the /start command and sends a welcome message to the user.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        None
    """
    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat.id

    if user_id not in user_data_dict:
        try:
            username = generate_username()
            # Initialize new user data
            new_user_data = {
                "user_id": int(user_id),
                "chat_id": chat_id,
                "username": username,
                "email": None,
                "phone": None,
                "status_message_id": None,
                "active": False
            }

            # Add the new user data to user_data_dict
            user_data_dict[user_id] = new_user_data

            # Save the updated user_data_dict to a JSON file
            save_to_json(user_data_dict, 'user_data.json')

        except Exception as error:
            logging.error("An error occurred while generating username: %s", error)
            update.message.reply_text("An error occurred. Please try again.")
            return

        logging.info("New user started the bot. user_id: %s", user_id)
        update.message.reply_text(
            f"Welcome! Your default username is {username}. Type /activate to begin receiving updates."
        )
    else:
        username = user_data_dict[user_id]['username']
        if user_data_dict[user_id]['active']:
            activate_text = "Type /deactivate to stop receiving updates."
        else:
            activate_text = "Type /activate to receive updates."
        update.message.reply_text(f"Welcome back, {username}! {activate_text}")

def activate(update: Update, context: CallbackContext) -> None:
    """
    Activates real-time updates for the user.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        None
    """
    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return

    # Fetch the current activation status from user_data_dict
    current_activation = user_data_dict[user_id]['active']

    if not current_activation:
        try:
            user_data_dict[user_id]['active'] = True
            save_to_json(user_data_dict, 'user_data.json')
        except Exception as error:
            logging.error("An error occurred while activating updates for user %s: %s", user_id, error)
            update.message.reply_text("An error occurred. Please try again.")
            return
        logging.info("Activated real-time updates for user %s.", user_id)
        update.message.reply_text("Activated! You will now receive real-time updates.")
    else:
        update.message.reply_text("You are already receiving real-time updates.")

def deactivate(update: Update, context: CallbackContext) -> None:
    """
    Deactivates real-time updates for the user.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        None
    """
    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return

    # Fetch the current activation status from user_data_dict
    current_activation = user_data_dict[user_id]['active']

    if current_activation:
        try:
            user_data_dict[user_id]['active'] = False
            save_to_json(user_data_dict, 'user_data.json')
        except Exception as error:
            logging.error("An error occurred while deactivating updates for user_id %d: %s", user_id, error)
            update.message.reply_text("An error occurred. Please try again.")
            return
        logging.info("Deactivated real-time updates for user %s.", user_id)
        update.message.reply_text("Deactivated. You will no longer receive real-time updates.")
    else:
        update.message.reply_text("You are already not receiving real-time updates.")

def generate_username() -> str:
    """
    Generates a random username using a list of structured random nouns.

    Parameters:
        None

    Returns:
        str: A string containing the generated username.
    """
    try:
        with open('./structured_random_nouns.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)
            random_nouns = data['words']
    except FileNotFoundError:
        logging.error("structured_random_nouns.json file not found.")
        return "An error occurred while generating your username. Please try again."
    except json.JSONDecodeError:
        logging.error("structured_random_nouns.json file has an invalid format.")
        return "An error occurred while generating your username. Please try again."

    username = f'Black {random.choice(random_nouns)}'
    logging.info("Generated username: %s", username)
    return username

def change_username(update: Update, context: CallbackContext) -> str:
    """
    Handles the /username command and prompts the user to enter their new username.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        str: The next state in the conversation.
    """
    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return ConversationHandler.END

    # Fetch the current username from user_data_dict
    current_username = user_data_dict[user_id]['username']

    try:
        update.message.reply_text(f"Your current username is {current_username}. Please enter your new username.\n\n/cancel this operation")
        logging.info("Prompted user %s for new username.", user_id)
    except Exception as error:
        logging.error("An error occurred while prompting for new username: %s", error)
        update.message.reply_text("An error occurred. Please try again.")

    return "get_username"

def get_username(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's response to the /username command and updates their username.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        int: The next state in the conversation, or ConversationHandler.END to end it.
    """
    new_username = update.message.text.strip()
    user_id = str(update.message.from_user.id)

    try:
        # Validate new username
        if not new_username:
            update.message.reply_text("Username cannot be empty.\n\n/cancel this operation")
            return "get_username"

        # Update the username in the user_data_dict
        user_data_dict[user_id]['username'] = new_username

        # Save the updated user_data_dict to a JSON file
        save_to_json(user_data_dict, 'user_data.json')

        logging.info("User %s changed their username to %s", user_id, new_username)
        update.message.reply_text(f"Your username has been updated to {new_username}.")
    except Exception as error:
        logging.error("An error occurred while updating username: %s", error)
        update.message.reply_text("An error occurred. Please try again.")
    return ConversationHandler.END

def change_email(update: Update, context: CallbackContext) -> str:
    """
    Handles the /email command and prompts the user to enter their email address.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        str: The next state in the conversation.
    """
    context.user_data['field_to_clear'] = 'email'

    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return ConversationHandler.END

    # Fetch the user's current e-mail from user_data_dict
    current_email = user_data_dict[user_id]['email']

    try:
        update.message.reply_text(f"Your current email address is {current_email}. Please enter your new email address.\n\n/clear your email address\n/cancel this operation")
        logging.info("Prompted user %s for email address.", user_id)
    except Exception as error:
        logging.error("An error occurred while prompting for email: %s", error)
        update.message.reply_text("An error occurred. Please try again.")

    return "get_email"

def get_email(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's response to the /email command and validates their email address.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        int: The next state in the conversation, or ConversationHandler.END to end it.
    """

    new_email = update.message.text.strip()
    user_id = str(update.message.from_user.id)

    try:
        # Validate email address
        if not re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})+", new_email):
            update.message.reply_text("Invalid email address. Please try again.\n\n/clear your email address\n/cancel this operation")
            return "get_email"

        # Update the email address in the user_data_dict
        user_data_dict[user_id]['email'] = new_email

        # Save the updated user_data_dict to a JSON file
        save_to_json(user_data_dict, 'user_data.json')

        logging.info("User %s entered email address: %s", user_id, new_email)
        update.message.reply_text(f"Your email address has been saved as {new_email}.")
    except Exception as error:
        logging.error("An error occurred while saving email: %s", error)
        update.message.reply_text("An error occurred. Please try again.")
    return ConversationHandler.END

def change_phone(update: Update, context: CallbackContext) -> str:
    """
    Handles the /phone command and prompts the user to enter their phone number.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        str: The next state in the conversation.
    """
    context.user_data['field_to_clear'] = 'phone'

    user_id = str(update.message.from_user.id)

    # Check if this user_id already exists in user_data_dict
    if user_id not in user_data_dict:
        update.message.reply_text("Please use the /start command to initialize your profile.")
        return ConversationHandler.END

    # Fetch the user's current phone number from user_data_dict
    current_phone = user_data_dict[user_id]['phone']
    if current_phone is not None:
        formatted_phone = current_phone[:3] + '-' + current_phone[3:6] + '-' + current_phone[6:]
    else:
        formatted_phone = "not yet entered"

    try:
        update.message.reply_text(f"Your current phone number is {formatted_phone}. Please enter your new phone number.\n\n/clear your phone number\n/cancel this operation")
        logging.info("Prompted user %s for phone number.", user_id)
    except Exception as error:
        logging.error("An error occurred while prompting for phone number: %s", error)
        update.message.reply_text("An error occurred. Please try again.")

    return "get_phone"


def get_phone(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's response to the /phone command and validates their phone number.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        int: The next state in the conversation, or ConversationHandler.END to end it.
    """
    new_phone = update.message.text.strip()
    user_id = str(update.message.from_user.id)

    # Remove any non-numeric characters
    new_phone = re.sub(r"[^\d]", "", new_phone)

    # Validate the phone number using a regular expression
    if not re.match(r"^[0-9]{10}$", new_phone):
        update.message.reply_text("Invalid phone number. Please try again.\n\n/clear your phone number\n/cancel this operation")
        return "get_phone"

    try:
        # Update the phone number in the global dictionary
        user_data_dict[user_id]['phone'] = new_phone
        save_to_json(user_data_dict, 'user_data.json')
        logging.info(
            "User %s entered phone number: %s", 
            user_id, new_phone
        )
        formatted_phone = new_phone[:3] + '-' + new_phone[3:6] + '-' + new_phone[6:]
        update.message.reply_text(f"Your phone number has been saved as {formatted_phone}.")
    except Exception as error:
        logging.error("An error occurred while saving phone number: %s", error)
        update.message.reply_text("An error occurred. Please try again.")
    return ConversationHandler.END

def clear(update: Update, context: CallbackContext) -> int:
    """
    Clears the specified field (either email or phone) for the user in the conversation.
    The field to clear is determined by the 'field_to_clear' value in context.user_data,
    which should be set in the entry function of the ConversationHandler

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback,
                                                containing the 'field_to_clear' in user_data.

    Returns:
        int: ConversationHandler.END to end the conversation.
    """
    user_id = str(update.message.from_user.id)

    field_to_clear = context.user_data.get('field_to_clear', None)

    if field_to_clear:
        user_data_dict[user_id][field_to_clear] = None
        save_to_json(user_data_dict, 'user_data.json')
        if field_to_clear == 'phone':
            formatted_field = 'phone number'
        else:
            formatted_field = 'email address'
        update.message.reply_text(f"Your {formatted_field} has been cleared.")
    else:
        update.message.reply_text("An error occurred. No field specified to clear.")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Handles the /cancel command and cancels the conversation handler.

    Parameters:
        update (telegram.Update): The update object for the command.
        context (telegram.ext.CallbackContext): The context object for the callback.

    Returns:
        int: The next state in the conversation, or ConversationHandler.END to end it.
    """
    try:
        update.message.reply_text("Operation cancelled.")
        logging.info("User %d cancelled the operation.", update.message.from_user.id)
    except Exception as error:
        logging.error("An error occurred while cancelling the operation: %s", error)
        update.message.reply_text("An error occurred. Please try again.")
    return ConversationHandler.END

def signal_handler(sig, frame):
    """
    Handles Unix signals to gracefully terminate the application.

    Parameters:
        sig: The signal number.
        frame: The current stack frame (not used).

    Returns:
        None
    """
    logging.info("Exiting the application...")
    sys.exit(0)

def help_command(update: Update, context: CallbackContext):
    """
    Handles the /help command and sends a list of available commands to the user.

    Parameters:
        update (telegram.Update): The update object for the command.

    Returns:
        None
    """
    try:
        help_text = "Available commands:\n\n"
        help_text += "/activate - Activate real-time updates.\n"
        help_text += "/deactivate - Stop receiving updates.\n"
        help_text += "/username - Customize your username.\n"
        help_text += "/email - Toggle email alerts.\n"
        help_text += "/phone - Toggle text alerts.\n"
        help_text += "/repost - Repost current job status.\n"
        help_text += "/start - Register new user."

        update.message.reply_text(help_text)
        logging.info("Sent help text to user %d.", update.message.from_user.id)
    except Exception as error:
        logging.error("An error occurred while sending help text: %s", error)
        update.message.reply_text("An error occurred. Please try again.")

def setup_command_handlers(updater):
    """
    Sets up command and conversation handlers.

    Parameters:
        updater (telegram.ext.Updater): The Updater object for the bot.

    Returns:
        None
    """
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    activate_handler = CommandHandler("activate", activate)
    dispatcher.add_handler(activate_handler)

    deactivate_handler = CommandHandler('deactivate', deactivate)
    dispatcher.add_handler(deactivate_handler)

    conv_handler_username = ConversationHandler(
        entry_points=[CommandHandler('username', change_username)],
        states={
            "get_username": [MessageHandler(Filters.text & ~Filters.command, get_username)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler_username)

    conv_handler_email = ConversationHandler(
        entry_points=[CommandHandler('email', change_email)],
        states={
            "get_email": [MessageHandler(Filters.text & ~Filters.command, get_email)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('clear', clear)]
    )
    dispatcher.add_handler(conv_handler_email)

    conv_handler_phone = ConversationHandler(
        entry_points=[CommandHandler('phone', change_phone)],
        states={
            "get_phone": [MessageHandler(Filters.text & ~Filters.command, get_phone)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('clear', clear)]
    )
    dispatcher.add_handler(conv_handler_phone)

    repost_handler = CommandHandler('repost', repost)
    dispatcher.add_handler(repost_handler)

    help_handler = CommandHandler("help", help_command)
    dispatcher.add_handler(help_handler)

def main():
    """
    Initializes the Telegram bot and starts the polling process.
    
    Returns:
        None
    """
    try:
        env_vars = fetch_environment_variables()
        if 'TELEGRAM_BOT_TOKEN' not in env_vars:
            logging.error(
                "TELEGRAM_BOT_TOKEN not found in environment variables."
            )
            sys.exit(1)

        bot_token = env_vars['TELEGRAM_BOT_TOKEN']
        updater = Updater(token=bot_token, use_context=True)

        # Setup command handlers
        setup_command_handlers(updater)

        # Start threading functions
        start_send_updates_thread(updater.dispatcher)

        # Register the signal handler
        signal.signal(signal.SIGINT, signal_handler)

        logging.info("Bot started. Press Ctrl+C to exit.")
        updater.start_polling()

    except Exception as error:
        logging.error("An error occurred while initializing the bot: %s", error)

if __name__ == '__main__':
    main()
