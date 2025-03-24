
from datetime import datetime
import jdatetime
import html
import json
import traceback

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


from config import Config
from handlers.constants.buttons import BTN
from handlers.constants.callback_data import CD
from handlers.constants.keyboards import Keyboards
from handlers.constants.messages import Messages
from db.models import User, ForcedJoinChannelOrder
from handlers.deep_links import deep_link_manager
from handlers.utils.utils import is_admin, is_bot_admin_in_channel
from handlers.utils.utils import check_if_user_is_joined_channels
from handlers.utils.user_info import UserFunctionalities


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        
        # print(datetime.now(tz=Config.TIMEZONE))
        # print(jdatetime.datetime.now())

        user = update.effective_user
        

        
        

        db_user, newly_created = await UserFunctionalities.get_or_create_user_in_db_for_start(tg_user=user)

        user_functionalities = await UserFunctionalities.create(
            context = context,
            db_user = db_user,
            newly_created = newly_created
        )
        context.user_data['user_functionalities'] = user_functionalities

        has_just_started = False
        if db_user.has_started == False:
            has_just_started = True
            db_user.has_started = True
            await db_user.save()
            
        if is_admin(user):
            # print(dir(update.message))  # Print all attributes of the message object

            return await update.message.reply_text(
                 "سلام جیگر!", 
                 reply_markup=ReplyKeyboardMarkup(Keyboards.ADMIN_START_KEYBOARD))
        


        context.application.create_task(
            deep_link_manager(
                context=context, 
                update=update, 
                user_functionalities=user_functionalities, 
                has_just_started = has_just_started
                )
            )


        
        is_member_in_all, details, couldnt_check, selected_channels = await check_if_user_is_joined_channels(update, context)

        if not is_member_in_all:
            inline_keyboard = []
            for channel in selected_channels:
                if channel.channel_id in details and details[channel.channel_id] == True:
                    continue
                inline_keyboard.append([InlineKeyboardButton(text=channel.title, url=channel.link)])

            inline_keyboard.append([InlineKeyboardButton(text="✅ عضو شدم ✅", callback_data=CD.I_JOIN_IN_ALL)])
            await update.effective_chat.send_message(text= Messages.JOIN_TO_USE, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            
            return
        
        keyboard = ReplyKeyboardMarkup([
            [
                BTN.MY_BALANCE, 
                BTN.REFERRAL_INFO,
                # "❤️ راهنمای ربات", 
                # "🗃 چنل آرشیو"
                ]
            
            ], resize_keyboard= True)
        await update.message.reply_text(
            Messages.START.format(user.first_name),
            reply_markup = keyboard, 
            parse_mode=ParseMode.MARKDOWN_V2
        )


async def there_is_no_such_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('چنین دستوری تعریف نشده است')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )



    chat_id = Config.MAJOR_ERRORS_CHANNEL


    # no need to report blocks
    if "Forbidden: bot was blocked by the user" in tb_string:

        
        db_user = await UserFunctionalities.get_db_user(tg_user=update.effective_user)

        db_user.has_blocked_the_bot = True
        return await db_user.save()
        

    old_query = "Query is too old and response timeout expired"
    user_button_double_tap = "specified new message content and reply markup are exactly the same as a current content"
    if (user_button_double_tap in tb_string) or (old_query in tb_string):
        ## not sending an error message if the error is caused by the user double tap
        chat_id = Config.MINOR_ERRORS_CHANNEL
    

    try:
        # Finally, send the message
        await context.bot.send_message(
            chat_id=chat_id, text=message, parse_mode=ParseMode.HTML
        )
    except:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=(
                "An exception was raised while handling an update\n"
                f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
                f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
                f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
                ),
            parse_mode=ParseMode.HTML
            )
        # await context.bot.send_message(
        #     chat_id=chat_id, text=f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n",
        #     parse_mode=ParseMode.HTML
        #     )
        # await context.bot.send_message(
        #     chat_id=chat_id, text=f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n",
        #     parse_mode=ParseMode.HTML
        #     )
        # await context.bot.send_message(
        #     chat_id=chat_id, text=f"<pre>context.user_data = {html.escape(str(tb_string))}</pre>\n\n",
        #     parse_mode=ParseMode.HTML
        #     )
        chunk_size = 4000  # Leave some buffer for extra characters
        msg = str(tb_string)
        for i in range(0, len(msg), chunk_size):
            await context.bot.send_message(
                chat_id=chat_id, text=msg[i : i + chunk_size]
            )
        
