
import datetime
import random
import re
import string
from typing import List, Optional, Tuple
from urllib.parse import urlparse
import telegram
from telegram import ChatMember, Document, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation, InputMediaAudio, InputMediaPhoto, InputMediaVideo, Update, Message as TGMessage, Video, Audio, Animation
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus, ParseMode

from tortoise.transactions import atomic

from config import Config
from db.models import ChannelMembership, ForcedJoinChannelOrder, InstagramRequest, Settings, SubscriptionPlan, User, UserBalance, UserSubscriptionPlan, Message
from handlers.constants.callback_data import CD
from handlers.constants.messages import Messages
from handlers.utils.pydanticmodels import MessageKeyboard
from handlers.utils.user_info import UserFunctionalities

def querify(*args):
    """
    mix data to make an effective callback data
    """
    args = map(str, args)
    return '/'.join(args)

def dequierify(callback_data:str):
    return callback_data.split('/')


def is_valid_url(text):
    parsed = urlparse(text)
    return bool(parsed.scheme and parsed.netloc)

def extract_status_change(chat_member_update: telegram.ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


def is_admin(user = None, user_id = None):
    if not user:
        return str(user_id) in Config.admins
    return str(user.id) in Config.admins





def extract_instagram_link_type_and_id(url: str) -> str:
    """
    Determines the type of Instagram request based on the given URL.

    :param url: The Instagram URL.
    :return: The request type (post, story, highlight, user, etc.) or "unknown".
    """
    for request_type, pattern in Config.INSTAGRAM_REGEX_PATTERNS.items():
        match = re.match(pattern, url)
        if match:
            groups = list(match.groups())  # Extracts all captured groups
            if request_type=="share" and groups[0]=='reels':
                groups[0]="reel"
            return (request_type, *groups)  # Expands tuple so all values are returned
    return None  # If no match, return "unknown"

# def extract_instagram_link_type_and_id(url):
#     """
#     Extracts the shortcode from an Instagram post URL.
    
#     :param url: str - Instagram post URL
#     :return: str or None - The extracted shortcode if found, otherwise None
#     """
#     pattern = Config.INSTAGRAM_REQUEST_LINK_REGEX
#     match = re.search(pattern, url)
    
#     if match:

#         request_type = 

#     return match.group(1), match if match else None

async def is_user_joined_in_channels(update: telegram.Update, context:ContextTypes.DEFAULT_TYPE, channel_ids:list):
    details = {} # True(member) / False(not member) / None(couldn't check membership)
    is_member_in_all = True
    couldnt_check = []

    user_id = update.effective_user.id
    for channel_id in channel_ids:
    
        try:
            # Check if the user is a member of the private channel
            chat_member = await context.bot.get_chat_member(channel_id, user_id)

            if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                # is member
                details[channel_id] = True
            else:
                # not joined
                is_member_in_all = False
                details[channel_id] = False

        except Exception as e:
            await report_in_channel(
                context=context,
                text= "❌❌❌❌ couldn't check membership"
            )
            # ❌ Could not check membership. Make sure the bot is an admin in the private channel.
            details[channel_id] = None
            couldnt_check.append(channel_id)

    return is_member_in_all, details, couldnt_check



async def check_if_user_is_joined_channels(update: telegram.Update, context:ContextTypes.DEFAULT_TYPE):
    
    settings = await Settings.first()
    max_number_of_forced_joins = settings.max_forced_channels
    channels = await ForcedJoinChannelOrder.filter(completion_status = False).limit(max_number_of_forced_joins).order_by('-is_fake_force').all()
    
    
    channel_ids = [channel.channel_id for channel in channels if not channel.is_fake_force]
    
    is_member_in_all, details, couldnt_check = await is_user_joined_in_channels(update, context, channel_ids)

    if(couldnt_check):
        for ch_id in couldnt_check:
            if not await is_bot_admin_in_channel(update=update,context=context,channel=ch_id):
                await report_in_channel(context=context, text=f"membership checker in {ch_id} is problematic because bot is not admin")
            


    return is_member_in_all, details, couldnt_check, channels
        

async def is_bot_admin_in_channel(update: telegram.Update, context:ContextTypes.DEFAULT_TYPE, channel):
    """Checks if the bot is an admin in the specified channel."""
    bot_id = context.bot.id  # Get the bot's own ID

    try:
        chat_member = await context.bot.get_chat_member(channel, bot_id)

        if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        else:
            return False

    except Exception as e:
            return None
    
async def report_in_channel(context:ContextTypes.DEFAULT_TYPE, text, chat_id = Config.REPORTS_CHANNEL):
    text = str(text)
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
    except:
        chunk_size = 4000
        for i in range(0, len(text), chunk_size):
            await context.bot.send_message(
                chat_id=chat_id, text=text[i : i + chunk_size]
            )


def inline_keyboard_with_two_btn_per_line(btn_list, query_prefix, highlight = []) -> List:
    """makes an inline keyboard with two btn per line
    highlights those btns whose values are in highlight list
        """
    keyboard = []
    keyboard_row = []

    for value in btn_list:
        # Determine the text, applying highlight if needed
        if highlight and (value in highlight):
            text = str(value) + "✅"
        else:
            text = str(value)
        
        # Append the button to the current row
        keyboard_row.append(InlineKeyboardButton(text=text, callback_data=querify(query_prefix, value)))
        
        # If the row now has 2 buttons, add it to the keyboard and reset the row
        if len(keyboard_row) == 2:
            keyboard.append(keyboard_row)
            keyboard_row = []

    # Append any leftover buttons (if the last row is not full)
    if keyboard_row:
        keyboard.append(keyboard_row)

    return keyboard

# @atomic()
# async def get_or_create_and_get_a_user(update: Update) -> User:
#     ef = update._effective_user
#     user = await User.filter(id = update.effective_user.id).first()

#     if not user:
#         user = User()
#         user.id = update.effective_user.id
#         user.first_name = update.effective_user.first_name
#         user.last_name = update.effective_user.last_name if update.effective_user.last_name else ''
#         user.is_bot = update.effective_user.is_bot
#         user.state = ''
#         user.has_started = False
#         user.role = User.ADMIN_USER if is_admin(ef) else User.GROUP_ANONYMOUS_BOT if (user.is_bot and update.effective_user.username == "GroupAnonymousBot") else User.NORMAL_USER 
            
#         await user.save()

#         default_subscription_plan = await SubscriptionPlan.filter(default_plan=True).first()
#         usp = UserSubscriptionPlan()
#         usp.ends_at = datetime.datetime.now(datetime.UTC)
#         usp.user = user
#         usp.subscription_plan = default_subscription_plan
#         await usp.save()


    
#     await user.fetch_related('user_subscription_plan')      
#     await user.user_subscription_plan.fetch_related('subscription_plan')

#     return user

# @atomic()
# async def get_or_create_and_get_a_user(
#     update: Update, 
#     has_started = False, 
#     is_from_accepter = False,
#     is_from_joining_a_chat = False
#     ) -> User:
#     ef = update.effective_user
#     user = await User.filter(id=update.effective_user.id) \
#                      .prefetch_related("user_subscription_plan__subscription_plan") \
#                      .first()

#     if not user:
#         user = User(
#             id=update.effective_user.id,
#             first_name=update.effective_user.first_name,
#             last_name=update.effective_user.last_name or '',
#             is_bot=update.effective_user.is_bot,
#             state='',
#             is_from_joining_a_chat = is_from_joining_a_chat,
#             has_started=has_started,
#             is_from_accepter = is_from_accepter,
#             role=(
#                 User.ADMIN_USER if is_admin(ef)
#                 else User.GROUP_ANONYMOUS_BOT if (update.effective_user.is_bot and update.effective_user.username == "GroupAnonymousBot")
#                 else User.NORMAL_USER
#             )
#         )
#         await user.save()

#         default_subscription_plan = await SubscriptionPlan.filter(default_plan=True).first()
#         usp = UserSubscriptionPlan(
#             ends_at=datetime.datetime.now(datetime.UTC),
#             user=user,
#             subscription_plan=default_subscription_plan
#         )
#         await usp.save()

#         # Reload the user with the prefetch.
#         user = await User.filter(id=update.effective_user.id) \
#                          .prefetch_related("user_subscription_plan__subscription_plan") \
#                          .first()

#     return user


# def user_subscription_plan(context) -> SubscriptionPlan:
#     return context.UDO.user_subscription_plan.subscription_plan
# def does_user_have_permission_to_do_this(context, request_type):
#     return request_type in user_subscription_plan(context=context).permitted_downloads
# async def rate_limit_info(context):
#     user_last_request = await InstagramRequest.filter(user__id = context.UDO.id).order_by('-created_at').first()
#     if not user_last_request:
#         return False, 0

#     usersp = user_subscription_plan(context=context)
#     time_since_last_req = datetime.datetime.now(datetime.UTC) - user_last_request.created_at
#     time_till_next_request = usersp.request_per_second_limit - time_since_last_req.seconds
#     rate_limit_has_passed = time_till_next_request > 0
#     return rate_limit_has_passed, time_till_next_request


def needs_force_join(function):
    async def wrapper(update, context, *args, **kwargs):
        is_member_in_all, details, couldnt_check, selected_channels = await check_if_user_is_joined_channels(update, context)
        if not is_member_in_all:
            inline_keyboard = []
            for channel in selected_channels:
                inline_keyboard.append([InlineKeyboardButton(text=channel.title, url=channel.link)])

            inline_keyboard.append([InlineKeyboardButton(text="✅ عضو شدم ✅", callback_data=CD.I_JOIN_IN_ALL)])
            await context.bot.send_message(chat_id = update.effective_chat.id, text= Messages.JOIN_TO_USE, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            return
        return await function(update, context, *args, **kwargs)
    
    return wrapper
    

async def create_a_db_message_from_tg_message(tg_msg:TGMessage) -> Message:
    
    new_msg = Message()
    
    
    
    entities = tg_msg.entities or tg_msg.caption_entities
    entities = [e.to_dict() for e in entities] if entities else None

    
    # if new_msg.is_forwarded:
    #     new_msg.origin_chat_id = tg_msg.forward_origin
    
    media = tg_msg.audio or tg_msg.animation or tg_msg.video or tg_msg.document or tg_msg.photo or None


    new_msg.is_forwarded = True if tg_msg.forward_origin else False
    new_msg.text = tg_msg.text or tg_msg.caption
    new_msg.entities = entities

    if media:
        if isinstance(media, Audio):
            mt = Message.MEDIA_TYPES.AUDIO
        elif isinstance(media, Video):
            mt = Message.MEDIA_TYPES.VIDEO
        elif isinstance(media, Animation):
            mt = Message.MEDIA_TYPES.GIF
        elif isinstance(media, Document):
            mt = Message.MEDIA_TYPES.DOCUMENT
        elif isinstance(media, tuple):
            mt = Message.MEDIA_TYPES.IMAGE
        else:
            mt = Message.MEDIA_TYPES.NONE

        new_msg.media_type = mt

        
        if mt == Message.MEDIA_TYPES.IMAGE:
            new_msg.media_id = media[-1].file_id
        else:
            new_msg.media_id = media.file_id
    

    # print(tg_msg.entities)
    new_msg.keyboard = []
    await new_msg.save()
    return new_msg

def get_telegram_reply_markup(db_keyboard:list, message_id, is_admin = False):
        

        db_keyboard = MessageKeyboard(rows=db_keyboard)
        keyboard = []
        for row_number, row in enumerate(db_keyboard.rows):
            new_row = []
            for btn in row:
                new_row.append(InlineKeyboardButton(
                    **btn
                ))

            if is_admin:
                new_row.append(
                    InlineKeyboardButton(
                        text= "+",
                        callback_data= querify(CD.NEW_BTN, message_id, row_number)
                    )
                )
            keyboard.append(new_row)
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton(
                        text= "+",
                        callback_data= querify(CD.NEW_BTN, message_id, 'N')
                    )]
            )

        keyboard = InlineKeyboardMarkup(keyboard)

        return keyboard
    
async def send_a_db_message(
        context: ContextTypes.DEFAULT_TYPE, 
        chat_id:int, 
        db_msg: Message | List[Message],
        # keyboard: InlineKeyboardMarkup | list = None
        ):

    if isinstance(db_msg, list):
        for msg in db_msg:
            await send_a_db_message(context, chat_id, msg)
        return
    
    keyboard = get_telegram_reply_markup(
            db_keyboard= db_msg.keyboard,
            message_id= db_msg.id,
            is_admin= is_admin(user_id=chat_id)
        )
        
    """
    send a db_message or a List of db_message s
    
    """
    
    entities = db_msg.entities if db_msg.entities else None

    if db_msg.media_type == db_msg.MEDIA_TYPES.VIDEO:
        return await context.bot.send_video(
            chat_id= chat_id,
            video= db_msg.media_id,
            caption= db_msg.text,
            reply_markup= keyboard,
            caption_entities= entities
        )
    elif db_msg.media_type == db_msg.MEDIA_TYPES.IMAGE:
        return await context.bot.send_photo(
            chat_id= chat_id,
            photo= db_msg.media_id,
            caption= db_msg.text,
            reply_markup= keyboard,
            caption_entities= entities
        )
    elif db_msg.media_type == db_msg.MEDIA_TYPES.GIF:
        return await context.bot.send_animation(
            chat_id= chat_id,
            animation= db_msg.media_id,
            caption= db_msg.text,
            reply_markup= keyboard,
            caption_entities= entities
        )
    elif db_msg.media_type == db_msg.MEDIA_TYPES.AUDIO:
        return await context.bot.send_audio(
            chat_id= chat_id,
            audio= db_msg.media_id,
            caption= db_msg.text,
            reply_markup= keyboard,
            caption_entities= entities,
            
        )
    elif db_msg.media_type == db_msg.MEDIA_TYPES.DOCUMENT:
        return await context.bot.send_document(
            chat_id= chat_id,
            document= db_msg.media_id,
            caption= db_msg.text,
            reply_markup= keyboard,
            caption_entities= entities,
            
        )
    elif db_msg.media_type == db_msg.MEDIA_TYPES.NONE:
        return await context.bot.send_message(
            chat_id= chat_id,
            text= db_msg.text,
            reply_markup= keyboard,
            entities=entities
        )

        
def number_to_telegram_emojis(number):
    """
    Converts a number into a string of keycap number emojis.
    
    For example:
      123 -> "1️⃣2️⃣3️⃣"
      
    :param number: The number to convert (can be int, float, or str).
    :return: A string with the number represented as emojis.
    """
    mapping = {
        '0': '0️⃣',
        '1': '1️⃣',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣',
        '.': '🔸'  # You can choose any emoji to represent a decimal point
    }
    
    # Convert the input to a string and replace each character with its emoji if available.
    return ''.join(mapping.get(char, char) for char in str(number))



async def create_btn(
        context: ContextTypes.DEFAULT_TYPE,
        update:Update,
        message_id: int,
        row_number: int|str,
        btn_text:str,
        btn_type:str,
        extra_info: str|int, # defines what happens when the btn is clicked. e.g. a msg id/link to be send 
):
    
    msg = await Message.filter(id = message_id).first()
            
    new_btn = {"text": btn_text,}
    
    if btn_type == "msg":
        msg_to_be_sent = extra_info
        new_btn["callback_data"] = querify(CD.SHOW_DB_MESSAGE, msg_to_be_sent)
    elif btn_type == "link":
        link = extra_info
        new_btn['url'] = link

    

    if row_number == "N":
        msg.keyboard.append([new_btn])
    else:
        msg.keyboard[int(row_number)].append(new_btn)

    await msg.save()

    await send_a_db_message(
        context=context,
        chat_id= update.effective_chat.id,
        db_msg= msg
            
    )

async def get_order_stats_msg(order_id):
            order = await ForcedJoinChannelOrder.get(id=order_id)

            done = await ChannelMembership.filter(
                joined_at__isnull = False,
                left_at__isnull = True,
                joined_from_link__startswith = order.link[:20]
            ).count()
            joined = await ChannelMembership.filter(
                joined_at__isnull = False,
                # left_at__isnull = True,
                joined_from_link__startswith = order.link[:20]
            ).count()
            left = await ChannelMembership.filter(
                left_at__isnull = False,
                joined_from_link__startswith = order.link[:20]
            ).count()

            completion_status = "✅" if order.completion_status else "❌"
            completion_status_text = "تکمیل شده" if order.completion_status else "در حال انجام"

            msg = Messages.ORDER_STATS.format(
                order.link,
                order.number_of_ordered_members,
                done,
                order.number_of_ordered_members - done,
                completion_status,
                completion_status_text,
                joined,
                left,
            )

            return msg

def give_them_loyalty_gift(function):

    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_funcs:UserFunctionalities = context.user_data['user_functionalities']
        if user_funcs.activity_manager.is_this_todays_first_interaction():
            settings:Settings = context.bot_data['settings']
            
            context.application.create_task(user_funcs.balance_manager.increase(
                currency_type = Config.CURRENCY_TYPES.GOLD_COIN,
                reason = Config.TRANSACTION_REASONS.LOYALTY_GIFT,
                amount = Config.TRANSACTION_AMOUNTS.LOYALTY_GIFT_COINS
            ))
            msg = "🎉🎉 به خاطر وفاداری شما به ربات به شما {} عدد سکه تعلق گرفت"
            await update.effective_chat.send_message(
                text= msg.format(number_to_telegram_emojis(Config.TRANSACTION_AMOUNTS.LOYALTY_GIFT_COINS))
            )
        return await function(update, context, *args, **kwargs)
    
    return wrapper


async def decrease_or_send_no_balance_message(
        context:ContextTypes.DEFAULT_TYPE,
        user_functionalities:UserFunctionalities,
        currency_type: str,
        reason: str,
        amount: int
        ):
    
    try:
        await user_functionalities.balance_manager.decrease(
                currency_type= currency_type,
                reason= reason,
                amount= amount
            )
    except:
        await context.bot.send_message(
            chat_id= user_functionalities.db_user.id,
            text= "متاسفانه شما موجودی کافی برای این کار ندارید. با یکی از روش های موجود موجودی خود را اضافه کنید"
        )