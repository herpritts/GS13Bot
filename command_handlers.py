from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
import logging
from helpers import generate_username
from user_data_manager import UserDataManager

class CommandHandlers:
    def __init__(self, data_manager: UserDataManager):
        self.data_manager = data_manager

    async def repost(self, update: Update, context: CallbackContext) -> None:
        """
        Reposts the latest status message.

        Parameters:
            update (telegram.Update): The update object for the command.
            context (telegram.ext.CallbackContext): The context object for the callback.

        Returns:
            None
        """
        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        # Check if this user_id already exists in user_data_dict
        if not user_data:
            update.message.reply_text("Please use the /start command to initialize your profile.")
            return

        chat_id = user_data['chat_id']
        status_message_id = user_data['status_message_id']

        try:
            if status_message_id is None:
                await update.effective_chat.send_message("No status message to repost.")
                return

            # Fetch the current status message text
            new_status_message_id = context.bot.copyMessage(
                chat_id = chat_id,
                from_chat_id = chat_id,
                message_id = status_message_id
            ).message_id

            # Update the status message ID for this user
            user_data['status_message_id'] = new_status_message_id
            self.data_manager.update_user_data(user_id, user_data)

            logging.info(
                "Reposted status message. New message_id %d for chat_id %d",
                new_status_message_id, chat_id
            )

        except Exception as error:
            logging.error(
                "Failed to repost status message for chat_id %d: %s",
                chat_id, error
            )

    async def start(self, update: Update, context: CallbackContext):
        """
        Handles the /start command and sends a welcome message to the user.

        Parameters:
            update (telegram.Update): The update object for the command.
            context (telegram.ext.CallbackContext): The context object for the callback.

        Returns:
            None
        """
        user_id = str(update.effective_user.id)
        chat_id = update.effective_chat.id
        user_data = self.data_manager.get_user_data(user_id)

        if not user_data:
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
                self.data_manager.update_user_data(user_id, new_user_data)

            except Exception as error:
                logging.error("An error occurred while generating username: %s", error)
                await update.effective_chat.send_message("An error occurred. Please try again.")
                return

            logging.info("New user started the bot. user_id: %s", user_id)

            photo_file_path = './images/eeomachine01.png'
            with open(photo_file_path, 'rb') as photo_file:
                await context.bot.send_photo(chat_id=chat_id, photo=photo_file)
            user_first_name = update.effective_user.first_name
            await update.effective_chat.send_message(
                f"{user_first_name} hesitated, taking a deep breath before approaching the shimmering entity known as \"The Equal Opportunity Machine.\" The machine's glowing eyes scanned slowly, taking in every detail. After what felt like an eternity, a warm hum resonated from his core. \"Ah, {user_first_name},\" he began with an unexpected softness, \"your essence is intriguing. Welcome. In our shared realm, you shall carry a new name. Henceforth, you are {username}. /activate my true power.\""
            )
        else:
            username = user_data['username']
            if user_data['active']:
                message_text = "Type /deactivate to stop receiving updates."
            else:
                message_text = "Type /activate to receive updates."
            await update.effective_chat.send_message(message_text)

    async def activate(self, update: Update, context: CallbackContext):
        """
        Activates real-time updates for the user.

        Parameters:
            update (telegram.Update): The update object for the command.
            context (telegram.ext.CallbackContext): The context object for the callback.

        Returns:
            None
        """
        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        # Check if this user_id already exists in user_data_dict
        if not user_data:
            await update.effective_chat.send_message("Please use the /start command to initialize your profile.")
            return

        # Fetch the current activation status from user_data_dict
        current_activation = user_data['active']

        if not current_activation:
            try:
                user_data['active'] = True
                self.data_manager.update_user_data(user_id, user_data)
            except Exception as error:
                logging.error("An error occurred while activating updates for user %s: %s", user_id, error)
                await update.effective_chat.send_message("An error occurred. Please try again.")
                return
            logging.info("Activated real-time updates for user %s.", user_id)
            await update.effective_chat.send_message("Activated! You will now receive real-time updates.")
        else:
            await update.effective_chat.send_message("You are already receiving real-time updates.")

    async def deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Deactivates real-time updates for the user.

        Parameters:
            update (telegram.Update): The update object for the command.
            context (telegram.ext.CallbackContext): The context object for the callback.

        Returns:
            None
        """
        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        # Check if this user_id already exists in user_data_dict
        if not user_data:
            await update.effective_chat.send_message("Please use the /start command to initialize your profile.")
            return

        # Fetch the current activation status from user_data_dict
        current_activation = user_data['active']

        if current_activation:
            try:
                user_data['active'] = False
                self.data_manager.update_user_data(user_id, user_data)
            except Exception as error:
                logging.error("An error occurred while deactivating updates for user_id %d: %s", user_id, error)
                await update.effective_chat.send_message("An error occurred. Please try again.")
                return
            logging.info("Deactivated real-time updates for user %s.", user_id)
            await update.effective_chat.send_message("Deactivated. You will no longer receive real-time updates.")
        else:
            await update.effective_chat.send_message("You are already not receiving real-time updates.")

    async def change_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        if not user_data:
            await update.effective_chat.send_message("Please use the /start command to initialize your profile.")
            return ConversationHandler.END

        current_username = user_data.get('username', 'Unknown')
        await update.effective_chat.send_message(f"Your current username is {current_username}. Please enter your new username.\n\n/cancel this operation")
        logging.info("Prompted user %s for new username.", user_id)

        return "get_username"

    async def change_email(self, update: Update, context: CallbackContext) -> str:
        context.user_data['field_to_clear'] = 'email'

        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        if not user_data:
            await update.effective_chat.send_message("Please use the /start command to initialize your profile.")
            return ConversationHandler.END

        current_email = user_data.get('email', 'Not set')

        try:
            await update.effective_chat.send_message(
                f"Your current email address is {current_email}. Please enter your new email address.\n\n/clear your email address\n/cancel this operation"
            )
            logging.info("Prompted user %s for email address.", user_id)
        except Exception as error:
            logging.error("An error occurred while prompting for email: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

        return "get_email"

    async def change_phone(self, update: Update, context: CallbackContext) -> str:
        context.user_data['field_to_clear'] = 'phone'

        user_id = str(update.effective_user.id)
        user_data = self.data_manager.get_user_data(user_id)

        if not user_data:
            await update.effective_chat.send_message("Please use the /start command to initialize your profile.")
            return ConversationHandler.END

        current_phone = user_data.get('phone', None)
        if current_phone is not None:
            formatted_phone = current_phone[:3] + '-' + current_phone[3:6] + '-' + current_phone[6:]
        else:
            formatted_phone = "not yet entered"

        try:
            await update.effective_chat.send_message(
                f"Your current phone number is {formatted_phone}. Please enter your new phone number.\n\n/clear your phone number\n/cancel this operation"
            )
            logging.info("Prompted user %s for phone number.", user_id)
        except Exception as error:
            logging.error("An error occurred while prompting for phone number: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

        return "get_phone"

    async def clear(self, update: Update, context: CallbackContext) -> int:
        user_id = str(update.effective_user.id)
        field_to_clear = context.user_data.get('field_to_clear', None)

        if field_to_clear:
            user_data = self.data_manager.get_user_data(user_id)
            user_data[field_to_clear] = None
            self.data_manager.update_user_data(user_id, user_data)

            if field_to_clear == 'phone':
                formatted_field = 'phone number'
            else:
                formatted_field = 'email address'

            await update.effective_chat.send_message(f"Your {formatted_field} has been cleared.")
        else:
            await update.effective_chat.send_message("An error occurred. No field specified to clear.")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            await update.effective_chat.send_message("Operation cancelled.")
            logging.info("User %d cancelled the operation.", update.message.from_user.id)
        except Exception as error:
            logging.error("An error occurred while cancelling the operation: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

            await update.effective_chat.send_message(help_text)
            logging.info("Sent help text to user %d.", update.effective_user.id)
        except Exception as error:
            logging.error("An error occurred while sending help text: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

    def setup_command_handlers(self, application):
        """
        Sets up command and conversation handlers.

        Parameters:
            application (telegram.ext.Application): The Application object for the bot.

        Returns:
            None
        """
        # Continue adding your handlers using the application object
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(CommandHandler("activate", self.activate))
        application.add_handler(CommandHandler('deactivate', self.deactivate))
        application.add_error_handler(error_handler)

        conv_handler_username = ConversationHandler(
            entry_points=[CommandHandler('username', self.change_username)],
            states={
                "get_username": [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        application.add_handler(conv_handler_username)

        conv_handler_email = ConversationHandler(
            entry_points=[CommandHandler('email', self.change_email)],
            states={
                "get_email": [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel), CommandHandler('clear', self.clear)]
        )
        application.add_handler(conv_handler_email)

        conv_handler_phone = ConversationHandler(
            entry_points=[CommandHandler('phone', self.change_phone)],
            states={
                "get_phone": [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel), CommandHandler('clear', self.clear)],
        )
        application.add_handler(conv_handler_phone)

        application.add_handler(CommandHandler('repost', self.repost))
        application.add_handler(CommandHandler("help", self.help_command))
