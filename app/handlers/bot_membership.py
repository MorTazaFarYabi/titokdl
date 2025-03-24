from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from handlers.constants.buttons import BTN
from handlers.constants.messages import Messages
from handlers.utils.user_info import UserFunctionalities
from handlers.utils.utils import querify, dequierify, extract_status_change, is_admin

from db.models import Channel, Group, User
from config import Config


import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



async def bot_was_added_to_a_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('added')
    user = update.effective_user
    chat = update.effective_chat

    

    if is_admin(user):
        # context.UDO.role = User.ADMIN_USER
        # await context.UDO.save()
        
        new_group = Group()
        new_group.id = chat.id
        new_group.title = chat.title
        new_group.admin = User(id = user.id)
        await new_group.save()
    else: 
        print('not admin')
        await context.bot.sendMessage(chat.id, Messages.YOU_CANT_USE_THIS_BOT.format(user.full_name))
        # await context.bot.sendMessage(Config.admins[0], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.title))
        # context.bot.sendMessage(Config.admins[1], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.id))
        await context.bot.leave_chat(chat_id=chat.id)
        await context.bot.send_message(Config.admins[0], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.title))
        # await context.bot.sendMessage(Config.admins[1], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.title))


    keyboard = [
        [
            InlineKeyboardButton(
                BTN.ACTIVATE_GROUP, 
                callback_data=querify(
                    BTN.CBD_ACTIVATE,
                    chat.id
                )),
        ],
        [
            InlineKeyboardButton(
                BTN.DEACTIVATE_GROUP, 
                callback_data=querify(
                    BTN.CBD_DEACTIVATE,
                    chat.id
                ))
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        user.id,
        Messages.BOT_SUCCESSFULLY_ADDED_TO_GROUP.format(chat.title), 
        reply_markup=reply_markup
    )
    



async def bot_was_removed_from_a_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("%s removed the bot from the group %s", update.effective_user.full_name, update.effective_chat.title)

    user = update.effective_user
    print(f"effective user: {user}")
    chat = update.effective_chat

    await Group.filter(id = chat.id).delete()
    await context.bot.send_message(user.id, Messages.GROUP_REMOVED.format(chat.title))

async def bot_was_added_to_a_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    cause = update.effective_user
    chat = update.effective_chat
    channel = await Channel.filter(id = chat.id).first()

    if is_admin(cause):
        # context.UDO.role = User.ADMIN_USER
        # await context.UDO.save()
        
        new_channel = Channel()
        new_channel.id = chat.id
        new_channel.title = chat.title
        new_channel.admin = User(id = cause.id)
        await new_channel.save()

    elif channel:
        return
    
    else: 
        await context.bot.sendMessage(chat.id, Messages.YOU_CANT_USE_THIS_BOT.format(cause.full_name))
        # await context.bot.sendMessage(Config.admins[0], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.title))
        # context.bot.sendMessage(Config.admins[1], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.id))
        await context.bot.leave_chat(chat_id=chat.id)
        await context.bot.send_message(Config.admins[0], Messages.USER_TRIED_TO_ADD_BOT_TO_CHANNEL.format(cause.full_name, chat.title))
        # await context.bot.sendMessage(Config.admins[1], Messages.USER_TRIED_TO_ADD_BOT_TO_GROUP.format(user.full_name, chat.title))


    await context.bot.send_message(
        cause.id,
        Messages.BOT_SUCCESSFULLY_ADDED_TO_CHANNEL.format(chat.title), 
    )
    

async def bot_was_removed_from_a_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("%s removed the bot from the CHANNEL %s", update.effective_user.full_name, update.effective_chat.title)

    user = update.effective_user
    chat = update.effective_chat

    await Channel.filter(id = chat.id).delete()


    if not user.is_bot: # if the bot didn't leave itself
        await context.bot.send_message(user.id, Messages.CHANNEL_REMOVED.format(chat.title))

async def track_bot_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tracks the chats the bot is in."""
        result = extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result

        # Let's check who is responsible for the change
        cause = update.effective_user
        cause_name = cause.full_name


        # Handle chat types differently:
        chat = update.effective_chat

        if chat.type == Chat.PRIVATE:
            uf:UserFunctionalities = context.user_data['user_functionalities']

            if not was_member and is_member:
                # This may not be really needed in practice because most clients will automatically
                # send a /start command after the user unblocks the bot, and start_private_chat()
                # will add the user to "user_ids".
                # We're including this here for the sake of the example.
                # user unblocked the bot

                
                uf.db_user.has_blocked_the_bot = False
                uf.db_user.has_started = True
                await uf.db_user.save()

            elif was_member and not is_member:
                # blocked the bot
                uf.db_user.has_blocked_the_bot = True
                await uf.db_user.save()
                
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            if not was_member and is_member:
                await bot_was_added_to_a_group(update, context)
            elif was_member and not is_member:
                await bot_was_removed_from_a_group(update, context)
        elif not was_member and is_member:
            # added the bot to the channel
            await bot_was_added_to_a_channel(update=update, context=context)

        elif was_member and not is_member:
            # removed the bot from the channel
            await bot_was_removed_from_a_channel(update=update, context=context)

