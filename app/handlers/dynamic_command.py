import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from handlers.constants.buttons import BTN
from handlers.constants.conversations import CONV
from handlers.constants.messages import Messages
from handlers.utils.statistics import get_statistics
from handlers.constants.keyboards import Keyboards
from db.models import ForcedJoinChannelOrder, Message as DatabaseMessage, DynamicCommand
from handlers.constants.callback_data import CD
from handlers.utils.utils import create_a_db_message_from_tg_message, is_bot_admin_in_channel, is_valid_url, querify, send_a_db_message



async def dynamic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    text = update.message.text  # Get the text sent by the user
    pattern = r"^\/([a-zA-Z0-9_]+)(?:@([a-zA-Z0-9_]+bot))?(?:\s(.+))?$"
    match = re.match(pattern, text)

    if match:
        command_name:str = match.group(1)  # The command name (without `/`)
        bot_name = match.group(2)  # The bot username (if provided)
        arguments = match.group(3)  # Any arguments after the command

        response = f"Command: {command_name}\nBot: {bot_name}\nArguments: {arguments}"
    # else:
    #     response = """چنین دستوری در ربات تعریف نشده است. لطفا روی دستور زیر کلیک کنید:"""
    #     await update.message.reply_text(response)

    
    command_in_db = await DynamicCommand.filter(command_name = command_name.lower()).first().prefetch_related('messages')

    if not command_in_db or len(command_in_db.messages) == 0:
        # if there is no such command OR the command has no messages set
        return await update.message.reply_text(
            text = "چنین دستوری تعریف نشده است. لطفا از /help استفاده کنید."
        )
    
    await send_a_db_message(
        context=context,
        chat_id=update.effective_chat.id,
        db_msg=list(command_in_db.messages)
    )

    print(update.message.text)
