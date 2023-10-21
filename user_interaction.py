import logging, re
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

class UserInteraction:
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})+")
    PHONE_REGEX = re.compile(r"^[0-9]{10}$")

    def __init__(self, data_manager):
        self.data_manager = data_manager

    async def update_user_data(self, update: Update, user_id: str, key: str, value: str) -> None:
        try:
            user_data = self.data_manager.get_user_data(user_id)
            user_data[key] = value
            self.data_manager.update_user_data(user_id, user_data)
        except Exception as error:
            logging.error("An error occurred while updating %s for user %s: %s", key, user_id, error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

    async def get_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        new_username = update.message.text.strip()
        user_id = str(update.effective_user.id)

        if not new_username:
            await update.effective_chat.send_message("Username cannot be empty.\n\n/cancel this operation")
            return "get_username"

        await self.update_user_data(update, user_id, 'username', new_username)

        logging.info("User %s changed their username to %s", user_id, new_username)
        await update.effective_chat.send_message(f"Your username has been updated to {new_username}.")

        return ConversationHandler.END

    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        new_email = update.message.text.strip()
        user_id = str(update.effective_user.id)

        try:
            # Validate email address
            if not self.EMAIL_REGEX.match(new_email):
                await update.effective_chat.send_message("Invalid email address. Please try again.\n\n/clear your email address\n/cancel this operation")
                return "get_email"

            # Update the email address in the user data
            await self.update_user_data(update, user_id, 'email', new_email)

            logging.info("User %s entered email address: %s", user_id, new_email)
            await update.effective_chat.send_message(f"Your email address has been saved as {new_email}.")
        except Exception as error:
            logging.error("An error occurred while saving email: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")

        return ConversationHandler.END

    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        new_phone = update.message.text.strip()
        user_id = str(update.effective_user.id)

        # Remove any non-numeric characters
        new_phone = re.sub(r"[^\d]", "", new_phone)

        # Validate the phone number using a regular expression
        if not self.PHONE_REGEX.match(new_phone):
            await update.effective_chat.send_message(
                "Invalid phone number. Please try again.\n\n/clear your phone number\n/cancel this operation"
            )
            return "get_phone"

        try:
            # Update the phone number in user_data
            await self.update_user_data(update, user_id, 'phone', new_phone)

            logging.info("User %s entered phone number: %s", user_id, new_phone)
            formatted_phone = new_phone[:3] + '-' + new_phone[3:6] + '-' + new_phone[6:]
            await update.effective_chat.send_message(f"Your phone number has been saved as {formatted_phone}.")
        except Exception as error:
            logging.error("An error occurred while saving phone number: %s", error)
            await update.effective_chat.send_message("An error occurred. Please try again.")
        return ConversationHandler.END
