import json
from typing import Any, List
from pydantic import BaseModel, TypeAdapter

from telegram import Message, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from config import Config
from db.models import APIReq, Channel, InstagramAccount, InstagramRequest, Message as DBMessage
from handlers.constants.callback_data import CD
from handlers.constants.messages import Messages
from handlers.constants.buttons import BTN
from handlers.utils.send_media import send_media
from handlers.utils.user_info import UserFunctionalities
from handlers.utils.utils import send_a_db_message
# from db.models import Group, User, Message

async def accepter_handler(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    ):

    
    
    user = update.chat_join_request.from_user
    channel = update.chat_join_request.chat
    invite_link = update.chat_join_request.invite_link.invite_link

    # print(f"user {user.full_name} requested to join {channel.title} using {invite_link}")
    
    db_channel = await Channel().filter(id = channel.id).first()

    context.application.create_task(
        UserFunctionalities.get_or_create_user_in_db_for_accepter(tg_user=update.effective_user)
    )

    if db_channel:
        await send_a_db_message(
            context = context,
            chat_id = update.effective_user.id,
            db_msg= await DBMessage.filter(id = db_channel.acceptor_message_id).first()
        )
    
    
    await context.bot.approve_chat_join_request(
        chat_id=update.effective_chat.id, user_id=update.effective_user.id
    )
