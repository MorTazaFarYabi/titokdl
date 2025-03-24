

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, Chat
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from handlers.constants.buttons import BTN
from handlers.constants.conversations import CONV
from handlers.constants.messages import Messages
from handlers.utils.statistics import get_statistics
from handlers.constants.keyboards import Keyboards
from db.models import Channel, ForcedJoinChannelOrder, Message as DatabaseMessage, DynamicCommand
from handlers.constants.callback_data import CD
from handlers.utils.utils import create_a_db_message_from_tg_message, create_btn, is_bot_admin_in_channel, is_valid_url, querify, send_a_db_message

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    keyboard = Keyboards.STATS_KEYBOARD

    await update.message.reply_text(text=await get_statistics(), reply_markup=InlineKeyboardMarkup(keyboard))


async def forced_join_control(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text=":::", reply_markup= ReplyKeyboardMarkup(Keyboards.CONTROL_FORCE_JOIN))


async def send_forced_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text="""channel_id
name
link
number_of_members
permanent => Yes/No
Fake => Yes/No
                                    
                                    
برای کنسل کردن /Cancel رو ارسال کنید""")
    return CONV.GET_ORDER_INFO


async def is_order_fake_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = ReplyKeyboardMarkup([[BTN.AP_FAKE_LINK, BTN.AP_FORCED_LINK]])
    await update.message.reply_text(text="✅ لطفا نوع سفارش خود را انتخاب کنید", reply_markup=keyboard)
    return CONV.GET_ORDER_TYPE

async def set_order_type_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    is_fake = True if update.message.text == BTN.AP_FAKE_LINK else False
    context.user_data["is_fake"] = is_fake
    context.user_data["ordered_members"] = 0 # when 0 the number is not tracked / if user wants tracking he will change it

    await update.message.reply_text(
        text= "🪧 عنوان لینک شیشه ای را ارسال کنید", 
        reply_markup= Keyboards.CANCEL_CONV
        )
    return CONV.GET_ORDER_TITLE
async def set_order_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    context.user_data["title"] = update.message.text

    if context.user_data['is_fake']:
        await update.message.reply_text(text= "🔗  لینک تبلیغ را ارسال کنید", reply_markup= Keyboards.CANCEL_CONV)
        return CONV.GET_ORDER_LINK
    else:
        await update.message.reply_text(
            text=Messages.ORDER_TRACKING_EXPLANATION, 
            reply_markup= Keyboards.CANCEL_CONV,
            parse_mode=ParseMode.HTML
            )
        return CONV.GET_ORDER_MEMBER_TRAKING_TYPE

async def set_order_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if not is_valid_url(update.message.text):
        message= """ل❌ لطفا لینک معتبری ارسال کنید   ✅ نمونه: https://t.me/+qdM51tTq8AQ5ZGFk"""
        await update.message.reply_text(
            text=message,
            reply_markup= Keyboards.CANCEL_CONV
            )
        return CONV.GET_ORDER_LINK
    
    user_data = context.user_data
    new_order = ForcedJoinChannelOrder()
    if user_data.get('channel_id'):
        new_order.channel_id = user_data['channel_id']
    new_order.is_fake_force = user_data['is_fake']
    new_order.title = user_data['title']
    new_order.link = update.message.text
    new_order.number_of_ordered_members = user_data['ordered_members']
    await new_order.save()

    await update.message.reply_text(text=Messages.ORDER_WAS_CREATED, reply_markup=ReplyKeyboardMarkup(Keyboards.ADMIN_START_KEYBOARD))
    context.user_data.clear()
    return ConversationHandler.END

async def set_order_tracking_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    number_of_members = update.message.text
    if not number_of_members.isdigit():
        await update.message.reply_text(text=Messages.SET_A_VALID_NUMBER_FOR_ORDER_TRACKING)
        return CONV.GET_ORDER_MEMBER_TRAKING_TYPE

    context.user_data["ordered_members"] = number_of_members

    if number_of_members == 0:
        await update.message.reply_text(text= "🔗  لینک تبلیغ را ارسال کنید")
        return CONV.GET_ORDER_LINK
    

    await update.message.reply_text(text=Messages.SEND_A_MESSAGE_FROM_CHANNEL)
    return CONV.SET_CHANNEL_INFO

async def set_order_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    origin = update.message.forward_origin
    if not (update.message and origin and hasattr(origin, "chat")):
        await update.message.reply_text("لطفا پیام معتبری را از چنلی که ربات در آن حتما عضو است فوروارد کنید")
        return CONV.SET_CHANNEL_INFO
    
    channel_id = origin.chat.id
    context.user_data["channel_id"] = channel_id
    

    if not await Channel.get_or_none(id = channel_id):
        await create_channel_in_db(
            update= update,
            context= context
        )

    if not await is_bot_admin_in_channel(update=update,context=context, channel= context.user_data["channel_id"]):
        await update.message.reply_text("❌ ربات در چنل ادمین نیست")
        return CONV.SET_CHANNEL_INFO
    
    await update.message.reply_text(
        text="آیا لینک خودکار ساخته شود؟", 
        reply_markup=ReplyKeyboardMarkup(
            [[
                BTN.AP_YES_AUTO_GENERATED_LINK, 
                BTN.AP_NO_READY_LINK
                ]]
            ))
    return CONV.IS_AUTO_GENERATED_LINK

async def is_auto_generated_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    channel_id = user_data['channel_id']

    if update.message.text == BTN.AP_NO_READY_LINK:
        await update.message.reply_text("لینکو بفرست")
        return CONV.GET_ORDER_LINK

    link = await context.bot.create_chat_invite_link(chat_id=channel_id)
    
    

    new_order = ForcedJoinChannelOrder()
    new_order.channel_id = channel_id
    new_order.is_fake_force = user_data['is_fake']
    new_order.title = user_data['title']
    new_order.link = link.invite_link
    new_order.number_of_ordered_members = int(user_data["ordered_members"])
    await new_order.save()

    await update.message.reply_text(text=Messages.ORDER_WAS_CREATED, reply_markup=ReplyKeyboardMarkup(Keyboards.ADMIN_START_KEYBOARD))
    context.user_data.clear()
    return ConversationHandler.END


async def get_back_to_admin_panel_main_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text="anjam shod", reply_markup=ReplyKeyboardMarkup(keyboard=Keyboards.ADMIN_START_KEYBOARD))


# async def get_order_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


#     channel_id, name, link, number_of_members, permanent, fake = update.message.text.split("\n")

#     if permanent.lower() == "yes":
#         permanent = True
#     else:
#         permanent= False

#     if fake.lower() == "yes":
#         fake = True
#     else:
#         fake= False

#     # link = await context.bot.createChatInviteLink(chat_id=channel_id)

#     new_order = ForcedJoinChannelOrder()
#     new_order.channel_id = channel_id
#     new_order.title = name
#     new_order.link = link
#     new_order.number_of_ordered_members = int(number_of_members)
#     new_order.fixed = permanent
#     new_order.is_fake_force = fake
#     await new_order.save()

#     await update.message.reply_text(text="اضاف شد")
#     return ConversationHandler.END

    


async def list_forced_channels_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    active_orders = await ForcedJoinChannelOrder.filter(completion_status = False).all()
    
    if not active_orders:
        await update.message.reply_text(text="چیزی برا نشون دادن نیست") 

    keyboard = []
    for order in active_orders:
        keyboard.append(
            [
            InlineKeyboardButton(text=order.title, url=order.link), 
            InlineKeyboardButton(text="❌", callback_data=querify(CD.DELETE_ORDER, order.id)),
            InlineKeyboardButton(text="✏️", callback_data=querify(CD.EDIT_ORDER, order.id))
            ]
                )

    await update.message.reply_text(text="list", reply_markup=InlineKeyboardMarkup(keyboard)) 

    

async def message_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="افزودن پیام", callback_data=CD.ADDING_NEW_MESSAGE), 
            InlineKeyboardButton(text="لیست پیام ها", callback_data=CD.LISTING_MESSAGES)
        ]
    ])
    message = "مدیریت پیام ها"
    await update.message.reply_text(
        text= message,
        reply_markup= keyboard
    )

async def add_the_new_msg_to_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    
    msg = await create_a_db_message_from_tg_message(update.message)

    await context.bot.send_message(chat_id=update.effective_chat.id, text= "انجام شد!")
    await send_a_db_message(
        context=context, 
        chat_id=update.effective_chat.id, 
        db_msg=msg)

    return ConversationHandler.END


async def broadcast_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    message = "ارسال های همگانی"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text = "🗄 لیست", callback_data= CD.LIST_BROADCASTS), 
            InlineKeyboardButton(text = "➕ ایجاد", callback_data= CD.ADD_NEW_BROADCAST)
            ]
    ])

    await update.message.reply_text(
        text= message,
        reply_markup=keyboard
    )

async def add_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    pass





async def source_link_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="افزودن لینک رهگیری", callback_data=CD.ADDING_NEW_SOURCE_LINK), 
            InlineKeyboardButton(text="لینک رهگیری", callback_data=CD.LISTING_SOURCE_LINKS)
        ]
    ])
    message = "مدیریت لینک های رهگیری"
    await update.message.reply_text(
        text= message,
        reply_markup= keyboard
    )


async def command_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="افزودن دستور", callback_data=CD.ADDING_NEW_COMMAND), 
            InlineKeyboardButton(text="لیست دستورات", callback_data=CD.LISTING_COMMANDS)
        ]
    ])
    message = "مدیریت دستورات"
    await update.message.reply_text(
        text= message,
        reply_markup= keyboard
    )

async def add_the_new_command_to_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    command_name = update.message.text.strip().strip('/')
    
    if len(command_name) > 40:
        return await update.effective_chat.send_message(
            text= "دستور فرستاده شده زیادی طولانیه از نو تلاش کن"
        )
    
    new_command = await DynamicCommand.create(
        command_name = command_name
    )
    await update.message.reply_text("دستور مد نظر با موفقیت ساخته شد. با استفاده از  بخش دستورات ویرایشش کن و به یه پیام متصلش کن")
    return ConversationHandler.END


async def channel_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user = update.effective_user
    channels = await Channel.all().order_by('-created_at')

    message = "لیست کانال های شما"

    keyboard = []
    for channel in channels:
        keyboard.append(
            [
                InlineKeyboardButton(text=channel.title, callback_data=querify(CD.CHANNEL_INFO, channel.id)),
                InlineKeyboardButton(text="❌", callback_data=querify(CD.CHANNEL_DELETE, channel.id)),
            ]
        )

    keyboard.append([
        InlineKeyboardButton(
            text= "+ افزودن",
            callback_data= CD.ADD_CHANNEL
        )
    ])

    await update.message.reply_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    

async def set_btn_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if not update.message.text:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= "لطفا عنوان معتبر را به صورت متنی بدون جزئیات اضافه بفرستید"
        )
    
    context.user_data['add_btn'].append(
        update.message.text
    )

    keyboard = [["msg", "link"]]
    
    await update.effective_chat.send_message(
        text= "لطفا نوع دکمه را انتخاب کنید",
        reply_markup= ReplyKeyboardMarkup(keyboard)
    )
    return CONV.SET_BTN_TYPE

            
async def set_btn_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    btn_types = ['msg', 'link']
    if not update.message.text or update.message.text not in btn_types:
        await update.message.reply_text("نوع معتبری انتخاب کنید")
        return CONV.SET_BTN_TYPE
    
    btn_type = update.message.text

    if btn_type == "msg":
        keyboard = []

        messages = await DatabaseMessage.all().limit(5).order_by('-created_at')
        if not messages:
            context.bot.send_message(chat_id=update.effective_chat.id, text= "no message in database")
            return ConversationHandler.END

        for message in messages:
            keyboard.append([
                            InlineKeyboardButton(
                                f"{message.id} انتخاب:", 
                                callback_data= querify(CD.CHOOSE_BTN_MESSAGE, message.id)
                                ),
                            InlineKeyboardButton(
                                text= "نمایش",
                                callback_data= querify(CD.SHOW_DB_MESSAGE, message.id)
                            )
                        ])

        pm = "انتخاب پیام دکمه"
                        
        await context.bot.send_message(
                            chat_id=update.effective_chat.id, 
                            text= pm, 
                            reply_markup= InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.HTML)

        return ConversationHandler.END
    elif btn_type == "link":
        await update.effective_chat.send_message("لینک دکمه را ارسال کنید")
        return CONV.SET_BTN_LINK
    
        

async def create_channel_in_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    origin = update.message.forward_origin
    if not (update.message and origin and hasattr(origin, "chat")):
        await update.message.reply_text("لطفا پیام معتبری را فوروارد کنید")
        return CONV.GET_CHANNEL_MSG
    

    channel: Chat = origin.chat

    db_channel = Channel()
    db_channel.id = channel.id
    db_channel.title = channel.title
    db_channel.admin_id = update.effective_user.id
    await db_channel.save()

    await update.effective_chat.send_message(
        text= "چنل به دیتابیس اضافه شد"
    )
    
    return ConversationHandler.END


async def set_btn_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if not is_valid_url(update.message.text):
        message= """ل❌ لطفا لینک معتبری ارسال کنید   ✅ نمونه: https://t.me/+qdM51tTq8AQ5ZGFk"""
        await update.message.reply_text(text=message)
        return CONV.SET_BTN_LINK
    
    message_id, row_number, btn_text = context.user_data['add_btn']

    await create_btn(
                context= context,
                update= update,
                message_id= message_id,
                row_number=row_number,
                btn_text= btn_text,
                btn_type= "link",
                extra_info= update.message.text
            )

    return ConversationHandler.END
    
