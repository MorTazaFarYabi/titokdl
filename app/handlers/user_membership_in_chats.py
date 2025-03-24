from datetime import UTC, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from handlers.constants.buttons import BTN
from handlers.constants.messages import Messages
from handlers.utils.user_info import UserFunctionalities
from handlers.utils.utils import querify, dequierify, extract_status_change, is_admin, report_in_channel

from db.models import Group, User, ChannelMembership, ForcedJoinChannelOrder
from config import Config


import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def track_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    # cause_name = update.chat_member.from_user.mention_html()
    # member_name = update.chat_member.new_chat_member.user.mention_html()

    cause_name = update.chat_member.from_user.full_name
    member_name = update.chat_member.new_chat_member.user.full_name

    if not was_member and is_member:
        
        
        # await update.effective_chat.send_message(
        #     f"{member_name} was added by {cause_name}. Welcome!",
        #     parse_mode=ParseMode.HTML,
        # )
        
        link = update.chat_member.invite_link.invite_link if update.chat_member.invite_link else None
        if not Config.IN_PRODUCTION:
            logger.info(f"{member_name} was added by {cause_name}. Welcome![{link}]")
        await user_was_added_to_chat(update, context)
    elif was_member and not is_member:
        
        # await update.effective_chat.send_message(
        #     f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
        #     parse_mode=ParseMode.HTML,
        # )
        if not Config.IN_PRODUCTION:
            logger.info(f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...")

        await user_left_the_chat(update, context)


async def user_was_added_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


    cm = update.chat_member

    if not cm.invite_link:
        if not Config.IN_PRODUCTION:
            logger.info("not from a join link")
        return
    
    link = cm.invite_link.invite_link.strip('.')
    
    order = await ForcedJoinChannelOrder.filter(link__startswith=link).first()
    if not order:
        if not Config.IN_PRODUCTION:
            logger.info(f'link does not exist in db [{link}]')

        return
        # the link the user joined from is not important

    user, newly_created = await UserFunctionalities.get_or_create_user_in_db_for_user_joined_chat(update.effective_user)

    new_membership = ChannelMembership()
    new_membership.channel_id = cm.chat.id
    new_membership.user = user
    new_membership.joined_at = datetime.now(tz=UTC)
    new_membership.joined_from_link = link
    new_membership.joined_from = ChannelMembership.JOINED_FROM_LINK
    
    try:
        await new_membership.save()

    except Exception as e:
        context.application.create_task(report_in_channel(
            context=context,
            text= f"❌ new membership save Error: {e}",
            chat_id= Config.MAJOR_ERRORS_CHANNEL
        ))
        

    if order.number_of_ordered_members == 0: # if the order is permanent
        return
        
    done = await ChannelMembership.filter(
                joined_at__isnull = False,
                left_at__isnull = True,
                joined_from_link__startswith = order.link[:20]
            ).count()

    if done >= order.number_of_ordered_members:
        order.completion_status = True
        await order.save()

async def user_left_the_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


    cm = update.chat_member

    membership = await ChannelMembership\
    .filter(
        user_id = cm.new_chat_member.user.id, 
        channel_id = cm.chat.id,
        left_at = None
        )\
    .order_by('-created_at').first()

    if membership:
        """
        - member joined the channel when the bot was tracking
        - membership = the last time they joined and didn't leave
        - if they joined before bot was the admin and there is no record for they join we wont enter this block
        """
        membership.left_at = datetime.now(tz=UTC)
        await membership.save()
        return

    else:
        if not Config.IN_PRODUCTION:
            logger.info("tracking user left is not important")
        return # tracking not important
    

    """
    if there is no join_record for the user:
    """

    user = await get_or_create_and_get_a_user(
        update= update,
        is_from_joining_a_chat= True
    )

    new_membership = ChannelMembership()
    new_membership.channel_id = cm.chat.id
    new_membership.user = user
    new_membership.joined_from = ChannelMembership.JOIN_FROM_UNKNOWN_SOURCE
    new_membership.joined_at = None
    new_membership.left_at = datetime.now(tz=UTC)
    
    try:
        await new_membership.save()
    except Exception as e:
        pass