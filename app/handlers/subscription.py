

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from handlers.constants.conversations import SUBP
from handlers.constants.buttons import BTN
from handlers.constants.messages import Messages
from handlers.constants.keyboards import Keyboards
from db.models import SubscriptionPlan, UserSubscriptionPlan
from handlers.constants.callback_data import CD
from handlers.utils.utils import querify

async def subscription_pannel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    
    await update.message.reply_text(text="مدیریت اشتراک ها", reply_markup=ReplyKeyboardMarkup(Keyboards.SUBSCRIPTION_PANNEL))

async def Subscription_plan_control(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    await update.message.reply_text(text="انتخاب کن ", reply_markup=ReplyKeyboardMarkup(Keyboards.SUBSCRIPTION_PLAN_CONTROL))


async def adding_subscription_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await update.message.reply_text(text="لطفا نام اشتراک را تعیین کنید مثلا: طلایی، نقره ای و...")

    return SUBP.SET_NAME

async def set_name_for_subscription_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if not update.message.text:
        
    #     return SUBP.SET_NAME

    context.user_data['subscription_name'] = update.message.text

    message = "آیا اشتراک {} مجبور به عضویت اجباری در کانال ها می شود؟".format(context.user_data['subscription_name'])
    await update.message.reply_text(
        text=message,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="بله", callback_data=querify(CD.FORCED_JOIN_FOR_SUBSCRIPTION, "yes")), 
                InlineKeyboardButton(text="خیر", callback_data=querify(CD.FORCED_JOIN_FOR_SUBSCRIPTION, "no"))]
        ])
        )
    return ConversationHandler.END

async def Subscription_plan_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    subscription_plans = await SubscriptionPlan.all()
    keyboard = []

    if not subscription_plans:
        return await update.message.text('هیچ پلنی نساختید')

    for sp in subscription_plans:
        keyboard.append(
            [
                InlineKeyboardButton(text=sp.name, callback_data=querify(CD.SUBSCRIPTION_PLAN_INFO, sp.id))
            ]
        )
    await update.message.reply_text(text="list", reply_markup=InlineKeyboardMarkup(keyboard))


async def set_subscription_plan_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args:str = " ".join(context.args)
    args = args.strip()
    args = args.split("=")

    if not len(args)==2:
        return await update.message.reply_text("دستور اشتباه است")
    
    id, new_name = args
    sp = await SubscriptionPlan().filter(id = id).first()
    if not sp:
        return await update.message.reply_text("چنین پلنی وجود نداره")
    
    sp.name = new_name
    await sp.save()

    await update.message.reply_text(text="اسم با موفقیت عوض شد", reply_markup=ReplyKeyboardMarkup(Keyboards.ADMIN_START_KEYBOARD))