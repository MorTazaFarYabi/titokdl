

import html
import json
import traceback

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, helpers
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


from config import Config
from handlers.constants.buttons import BTN
from handlers.constants.callback_data import CD
from handlers.constants.keyboards import Keyboards
from handlers.constants.messages import Messages
from db.models import Source, SourceClick, User, ForcedJoinChannelOrder, Referral
from handlers.utils.user_info import UserFunctionalities
# from handlers.utils.utils import get_or_create_and_get_a_user, is_admin, is_bot_admin_in_channel, report_in_channel
# from handlers.utils.utils import check_if_user_is_joined_channels


async def deep_link_manager(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        user_functionalities:UserFunctionalities, 
        has_just_started:bool
        ):

    payload = context.args

    if not payload:
        return

    parameter = payload[0]

    referred_functionalities = user_functionalities
    referred = referred_functionalities.db_user

    if parameter.startswith(Config.REFERRAL_DEEP_LINK_PREFIX):
        async def create_referral_item_in_db():
            _, referrer_id = parameter.split('_')

            referer = await UserFunctionalities.get_db_user(user_id=referrer_id)


            if referer.id == referred.id:
                await update.message.reply_text(
                    text= "🧐 !خودت نمیتونی زیرمجموعه خودت بشی که"
                )
                return
            
            if not referred_functionalities.is_a_new_comer:
                return


            

            referral = Referral()
            referral.referrer = referer
            referral.referred = referred
            await referral.save()

            
            

            async def increasing_referrer_balance():
                
                referrer_funcs = await UserFunctionalities.create(context=context, db_user=referer)

                await referrer_funcs.balance_manager.increase(
                    currency_type= Config.CURRENCY_TYPES.GOLD_COIN,
                    reason= Config.TRANSACTION_REASONS.REFERRAL,
                    amount= Config.TRANSACTION_AMOUNTS.REFERRAL_GIFT
                )

                await context.bot.send_message(
                chat_id= referer.id,
                text= f"🎉🎉 یک نفر با لینک شما به ربات پیوست. | جایزه شما: {Config.TRANSACTION_AMOUNTS.REFERRAL_GIFT} سکه"
                )

            context.application.create_task(increasing_referrer_balance())
        context.application.create_task(create_referral_item_in_db())

        
    # a specific deep link made for a source to track its stats 
        
    if parameter.startswith(Config.SOURCE_DEEP_LINK_PREFIX): # source stats (DLS)
        _, source_identifier = parameter.split('_')

        source = await Source.filter(identifier = source_identifier).first()

        if not await source:
            return # ignoring source clicks with no predefined source
        
        source_click = SourceClick()
        source_click.source = source
        source_click.user = user_functionalities.db_user
        await source_click.save()

    if parameter.startswith(Config.GIFT_DEEP_LINK_PREFIX):
        
        _, gift_type = parameter.split('_')

        if gift_type == "accepter":
            if has_just_started:
                ufuncs = user_functionalities
                await ufuncs.balance_manager.increase(
                    currency_type= Config.CURRENCY_TYPES.GOLD_COIN,
                    reason= Config.TRANSACTION_REASONS.GIFT,
                    amount= Config.TRANSACTION_AMOUNTS.GIFT_BTN_COINS
                )
                await update.message.reply_text(
                    text= "🎉🎉🎉🎉 هدیه {} سکه به حساب شما افزوده شد"
                )      
        
        
        



    
