from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your bot token and admin Telegram ID
BOT_TOKEN = "7582835217:AAGv-1S21HlbK3beALfvJw5lsCEEoHSBYPc"
ADMIN_ID = 2065823461  # Replace with your actual Telegram user ID

# Blocked users list
blocked_users = set()
reply_context = {}  # user_id to map forwarded messages

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to BunnyBot! Your messages will be forwarded to the admin.")

# User message handler
def user_message(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    if user_id in blocked_users:
        return  # Ignore messages from blocked users

    # Format the message
    text = update.message.text or ''
    message_text = f"<b>From:</b> {user.full_name} ({user_id})\n<code>#user_{user_id}</code>\n{text}"

    # Inline keyboard with reply and block options
    keyboard = [
        [InlineKeyboardButton("Reply", callback_data=f"reply_{user_id}"),
         InlineKeyboardButton("Block", callback_data=f"block_{user_id}")]
    ]

    # Send to admin with inline keyboard
    context.bot.send_message(chat_id=ADMIN_ID, text=message_text,
                             reply_markup=InlineKeyboardMarkup(keyboard),
                             parse_mode='HTML')
    
    # Forward actual message for reply context (optional)
    context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user_id, message_id=update.message.message_id)

# Admin reply logic
def admin_reply(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message

    # Case 1: Direct message using #user_123456789 format
    if msg.text and msg.text.startswith("#user_"):
        try:
            parts = msg.text.split(" ", 1)
            user_id = int(parts[0].replace("#user_", ""))
            text = parts[1] if len(parts) > 1 else ""
            context.bot.send_message(chat_id=user_id, text=f"<b>Admin:</b>\n{text}", parse_mode='HTML')
            msg.reply_text("Message sent successfully.")
            return
        except Exception as e:
            msg.reply_text(f"Error sending message: {e}")
            return

    # Case 2: Reply via Telegram's "reply to" feature
    if msg.reply_to_message:
        forwarded = msg.reply_to_message.forward_from
        if forwarded:
            user_id = forwarded.id
        elif 'user_id' in reply_context:
            user_id = reply_context.pop('user_id')
        else:
            msg.reply_text("Could not detect user to reply to.")
            return

        try:
            if msg.text:
                context.bot.send_message(chat_id=user_id, text=f"<b>Admin:</b>\n{msg.text}", parse_mode='HTML')
            elif msg.photo:
                context.bot.send_photo(chat_id=user_id, photo=msg.photo[-1].file_id, caption="Admin sent a photo.")
            elif msg.video:
                context.bot.send_video(chat_id=user_id, video=msg.video.file_id, caption="Admin sent a video.")
            msg.reply_text("Reply sent successfully.")
        except Exception as e:
            msg.reply_text(f"Failed to send message: {e}")

# Handle buttons (Reply or Block)
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data
    if data.startswith("reply_"):
        user_id = data.split("_")[1]
        reply_context['user_id'] = int(user_id)
        query.message.reply_text(f"Type your reply to {user_id} now:")
    elif data.startswith("block_"):
        user_id = int(data.split("_")[1])
        blocked_users.add(user_id)
        query.message.reply_text(f"User {user_id} has been blocked.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.chat(ADMIN_ID), admin_reply))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.chat(ADMIN_ID)), user_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
