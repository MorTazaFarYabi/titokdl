
import asyncio
from pydantic import TypeAdapter
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, helpers
import telegram
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import Config
from handlers.broadcast import broadcast_message
from handlers.constants.buttons import BTN
from handlers.constants.conversations import CONV
from handlers.constants.keyboards import Keyboards
from handlers.constants.messages import Messages
from handlers.constants.callback_data import CD
from handlers.others import instagram_downloader

from tortoise.functions import Count

from handlers.utils.statistics import (
    get_API_health_statistics, get_API_statistics, get_loyalty_statistics, 
    get_request_type_statistics, get_statistics, get_stats_by_creation_time,
    get_referral_statistics
    )
from handlers.utils.utils import check_if_user_is_joined_channels, create_btn, get_order_stats_msg, report_in_channel, send_a_db_message
from handlers.utils.one_api import InstagramAPI
from handlers.utils.pydanticmodels import Highlight, MediaItem, OneAPIResponse, Story
from handlers.utils.utils import inline_keyboard_with_two_btn_per_line, querify, dequierify

from db.models import BroadCastRequest, Channel, ChannelMembership, Group, Message, Source, SubscriptionPlan, User, ForcedJoinChannelOrder, DynamicCommand


import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



# Global registry to keep track of broadcast tasks
running_broadcasts = {}



async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    query = dequierify(update.callback_query.data)
    
    try:
        await update.callback_query.answer()
    except Exception as e:
        context.application.create_task(report_in_channel(
            context=context,
            text= "❌ QUERY PROBLEM: \n"+str(e),
            chat_id = Config.MINOR_ERRORS_CHANNEL
        ))
    
    match query[0]:
        case CD.CANCEL_CONV:
            await update.callback_query.edit_message_text("اوکی درخواست قبلی لغو شد")    
            return ConversationHandler.END
        case CD.I_JOIN_IN_ALL:

            is_member_in_all,_,_,_ = await check_if_user_is_joined_channels(update=update, context=context)
            if not is_member_in_all:
                return await context.bot.send_message(
                    chat_id= update.effective_chat.id,
                    text='❌ توی چنلای داده شده عضو نشدی❌')
            
            await update.callback_query.edit_message_text(Messages.START, parse_mode=ParseMode.MARKDOWN_V2)
            

        case BTN.CBD_GROUP_SETTING:
            group = await Group.get(id = query[1])
            title = group.title
            CA = group.is_comment_active
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(text = BTN.DEACTIVATE_GROUP if CA else BTN.ACTIVATE_GROUP, 
                                      callback_data=querify(BTN.CBD_DEACTIVATE, group.id) if CA 
                                      else querify(BTN.CBD_ACTIVATE, group.id))]])
            
            await update.callback_query.edit_message_text(Messages.GROUP_SETTING.format(title), reply_markup=markup)

        case CD.DELETE_ORDER:
            order = await ForcedJoinChannelOrder.get(id=query[1])

            await report_in_channel(
                context=context,
                text= await get_order_stats_msg(query[1]),
                chat_id= Config.FINANCE_CHANNEL
            )

            await order.delete()
            await update.callback_query.edit_message_text("hazf shod")

        case CD.EDIT_ORDER:
            order = await ForcedJoinChannelOrder.get(id=query[1])
            
            fixed = "بله" if order.number_of_ordered_members==0 else "نه"
            fake = "بله" if order.is_fake_force else "نه"


            message = Messages.FORCED_ORDER_INFO.format(
                order.channel_id, order.title, order.link, fixed, fake, " -", order.number_of_ordered_members
            )
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text= "آمار",
                            callback_data= querify(CD.ORDER_STATS, order.id)
                        )
                    ]
                ]
            )

            await update.callback_query.edit_message_text(
                message, 
                reply_markup= keyboard,
                parse_mode=ParseMode.HTML
                )

        case CD.ORDER_STATS:
            
            msg = await get_order_stats_msg(query[1])

            await update.callback_query.edit_message_text(
                text= msg
            )

        case CD.DL_STORIES:
            user_id_or_username = query[1]


            return await instagram_downloader(update=update, context=context, if_callback_query=True, download_info=(
                Config.INSTAGRAM_REUQEST_TYPES.STORIES,
                user_id_or_username,
                
            ))
            # instaAPI = InstagramAPI(Config.ONE_API_TOKEN)
            # one_api_response = await instaAPI.stories(user_id=user_id).fetch()
            # stories = TypeAdapter(list[MediaItem]).validate_python(one_api_response.result)

            
            # await send_media(update=update, context=context, media_list=stories)
            # story_urls = []
            # for story in one_api_response.result:
            #     story = Story(**story)
            #     story_urls.append(story.url)
            
            # print(story_urls)
            # await update.callback_query.edit_message_text(story_urls[0])

        case CD.DL_SINGLE_STORY:
            username = query[1]
            story_id = query[2]
            
            return await instagram_downloader(update=update, context=context, if_callback_query=True, download_info=(
                Config.INSTAGRAM_REUQEST_TYPES.STORY,
                username,
                story_id
            ))

        case CD.HIGHLIGHS_LIST:
            user_id = query[1]
            
            await instagram_downloader(update=update, context=context, if_callback_query=True, download_info=(
                Config.INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS,
                user_id
            ))

            # instaAPI = InstagramAPI(Config.ONE_API_TOKEN)
            # one_api_response = await instaAPI.highlights(user_id=user_id).fetch()
            # highlights = TypeAdapter(list[Highlight]).validate_python(one_api_response.result)

            # # keyboard = []
            # # keyboard_line = []
            # # for highlight in highlights:
            # #     if len(keyboard_line)==2:
            # #         keyboard.append(keyboard_line)
            # #         keyboard_line = []
            # #     else:
            # #         keyboard_line.append(InlineKeyboardButton(text=highlight.title, callback_data=querify(CD.DL_HIGHLIGHT, highlight.id)))

            # # await update.callback_query.edit_message_text(text="list", reply_markup=InlineKeyboardMarkup(keyboard))
            # await send_user_highlights(chat_id=update.effective_chat.id, context=context, highlights=highlights)
        case CD.DL_HIGHLIGHT:
            highlight_id = query[1].split(':')[1]
            await instagram_downloader(update=update, context=context, if_callback_query=True, download_info=(
                Config.INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES,
                highlight_id
            ))
            # instaAPI = InstagramAPI(Config.ONE_API_TOKEN)
            # one_api_response = await instaAPI.highlight(highlight_id=highlight_id).fetch()
            # stories = TypeAdapter(list[MediaItem]).validate_python(one_api_response.result)

            # await send_media(update=update, context=context, media_list=stories)

        case CD.FORCED_JOIN_FOR_SUBSCRIPTION:
            is_forced = True if query[1]=="yes" else False
            context.user_data['subscription_forced_join'] = is_forced

            keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="بله", callback_data=querify(CD.IS_SUBSCRIPTION_DEFAULT, "yes")), 
                InlineKeyboardButton(text="خیر", callback_data=querify(CD.IS_SUBSCRIPTION_DEFAULT, "no"))]
            ])
            await update.callback_query.edit_message_text(text="آیا این سابسکریپشن حالت دیفالت باشد؟", reply_markup=keyboard)

        case CD.IS_SUBSCRIPTION_DEFAULT:
            is_default = True if query[1]=="yes" else False
            context.user_data['is_subscription_default'] = is_default

            limit_list = Config.TIME_LIMIT_OPTIONS_FOR_SUBSCRIPTIONS

            keyboard=inline_keyboard_with_two_btn_per_line(limit_list, query_prefix=CD.SET_SUBSCRIPTION_LIMIT)
            

            await update.callback_query.edit_message_text(text="لیمیت دانلود های پیاپی بر اساس ثانیه", reply_markup=InlineKeyboardMarkup(keyboard))

        case CD.SET_SUBSCRIPTION_LIMIT:
            limit = query[1]
            context.user_data['subscription_limit'] = limit
            context.user_data['permitted_downloads'] = []

            items = [
                value for key, value in Config.INSTAGRAM_REUQEST_TYPES.__dict__.items()
                if not key.startswith('__')
            ]
            keyboard = inline_keyboard_with_two_btn_per_line(items, query_prefix=CD.PERMIT_DONWLOAD_TYPE)
            keyboard.append([
                InlineKeyboardButton(
                    text="🟩🟩 تمام 🟩🟩",
                    callback_data=CD.CREATE_SUBSCRIPTION_IN_DB
                )
            ])

            
            print(keyboard)

            await update.callback_query.edit_message_text(text="مطالب مجاز برای این اشتراک رو انتخاب کن", reply_markup=InlineKeyboardMarkup(keyboard))
        
        case CD.PERMIT_DONWLOAD_TYPE:
            permitted_type = query[1]
            highlights = context.user_data['permitted_downloads']
            highlights.append(permitted_type)
            items = [
                    value for key, value in Config.INSTAGRAM_REUQEST_TYPES.__dict__.items()
                    if not key.startswith('__')
                ]
            keyboard = inline_keyboard_with_two_btn_per_line(
                items, query_prefix=CD.PERMIT_DONWLOAD_TYPE, highlight=highlights
                )
            keyboard.append([InlineKeyboardButton(
                text= "🟩🟩 تمام 🟩🟩",
                callback_data= CD.CREATE_SUBSCRIPTION_IN_DB
            )])
            await update.callback_query.edit_message_text(text="مطالب مجاز برای این اشتراک رو انتخاب کن", reply_markup=InlineKeyboardMarkup(keyboard))
        
            
        case CD.CREATE_SUBSCRIPTION_IN_DB:
            ud = context.user_data
            if not ud['permitted_downloads']:
                items = [
                    value for key, value in Config.INSTAGRAM_REUQEST_TYPES.__dict__.items()
                    if not key.startswith('__')
                ]
                keyboard = inline_keyboard_with_two_btn_per_line(items, query_prefix=CD.PERMIT_DONWLOAD_TYPE)
                keyboard.append([InlineKeyboardButton(
                    text= "🟩🟩 تمام 🟩🟩",
                    callback_data= CD.CREATE_SUBSCRIPTION_IN_DB
                )])
                
                await update.callback_query.edit_message_text(text="""
❌ هیچ امکانی ندادی هنوز
مطالب مجاز برای این اشتراک رو انتخاب کن""", reply_markup=InlineKeyboardMarkup(keyboard))
            
                return
            
            sp = SubscriptionPlan()
            sp.name = ud['subscription_name']
            sp.does_see_forced_joins = ud['subscription_forced_join']
            sp.default_plan = ud['is_subscription_default']
            sp.request_per_second_limit = ud['subscription_limit']
            sp.permitted_downloads = ud['permitted_downloads']
            await sp.save()

            ud.clear()

            await update.callback_query.edit_message_text(text="سابسکریپشن با موفقیت ساخته شد")

        case CD.SUBSCRIPTION_PLAN_INFO:
            id = query[1]
            sp = await SubscriptionPlan.get(id=id)

            msg = Messages.SUBSCRIPTION_PLAN_INFO.format(
                sp.name, sp.request_per_second_limit, sp.does_see_forced_joins, sp.default_plan, ', '.join(sp.permitted_downloads)
            )

            keyboard = [
                [InlineKeyboardButton(text="📝 ویرایش اسم", callback_data=querify(CD.EDIT_SUBSCRIPTION_PLAN_NAME, sp.id))],
                [InlineKeyboardButton(text="📝 ویرایش لیمیت", callback_data=querify(CD.EDIT_SUBSCRIPTION_PLAN_LIMIT, sp.id))],
                [InlineKeyboardButton(text="📝 ویرایش اجبار عضویت", callback_data=querify(CD.EDIT_SUBSCRIPTION_PLAN_FORCE_JOIN, sp.id))],
                [InlineKeyboardButton(text="📝 تبدیل به پلن پیشفرض", callback_data=querify(CD.EDIT_SUBSCRIPTION_PLAN_DEFAULTNESS, sp.id))],
                ]
            await update.callback_query.edit_message_text(text=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

        case CD.EDIT_SUBSCRIPTION_PLAN_NAME:
            # /set_subscription_plan_name 1=برنزی
            id = query[1]

            await update.callback_query.edit_message_text("پیام زیر را کپی کنید و به جای -new- نام جدید را وارد کنید")
            await update.callback_query.edit_message_text("/set_subscription_plan_name {}=new".format(id))
            
        case CD.EDIT_SUBSCRIPTION_PLAN_LIMIT:
            limit_list = Config.TIME_LIMIT_OPTIONS_FOR_SUBSCRIPTIONS

            keyboard=[]
            for limit in limit_list:
                keyboard.append([InlineKeyboardButton(text=limit, callback_data=querify(CD.EDIT_SET_SUBSCRIPTION_PLAN_LIMIT, query[1], limit))])
            
            await update.callback_query.edit_message_text(text="تایم رو انتخاب کن تا ست شه", reply_markup=InlineKeyboardMarkup(keyboard))

        case CD.EDIT_SET_SUBSCRIPTION_PLAN_LIMIT:
            id = query[1]
            new_limit = query[2]
            await SubscriptionPlan.filter(id=id).update(request_per_second_limit=new_limit)
            await update.callback_query.edit_message_text(text="ست شد")
        case CD.EDIT_SUBSCRIPTION_PLAN_FORCE_JOIN:
            keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="بله", callback_data=querify(CD.EDIT_SET_SUBSCRIPTION_PLAN_FORCE_JOIN,query[1], "yes")), 
                InlineKeyboardButton(text="خیر", callback_data=querify(CD.EDIT_SET_SUBSCRIPTION_PLAN_FORCE_JOIN, query[1],"no"))]
            ])

            await update.callback_query.edit_message_text(text="مجبور شه جوین شه؟", reply_markup=keyboard)


        
        case CD.EDIT_SET_SUBSCRIPTION_PLAN_FORCE_JOIN:
            
            id = query[1]
            is_forced = True if query[2]=="yes" else False
            await SubscriptionPlan.filter(id=id).update(does_see_forced_joins=is_forced)
            await update.callback_query.edit_message_text(text="ست شد")

        case CD.EDIT_SUBSCRIPTION_PLAN_DEFAULTNESS:
            keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="بله", callback_data=querify(CD.EDIT_SET_SUBSCRIPTION_PLAN_DEFAULTNESS,query[1], "yes")), 
                InlineKeyboardButton(text="خیر", callback_data=querify(CD.EDIT_SET_SUBSCRIPTION_PLAN_DEFAULTNESS, query[1],"no"))]
            ])

            await update.callback_query.edit_message_text(text="دیفالت بشه؟", reply_markup=keyboard)

        case CD.EDIT_SET_SUBSCRIPTION_PLAN_DEFAULTNESS:
            id = query[1]
            is_default = True if query[2]=="yes" else False
            await SubscriptionPlan.filter(id=id).update(default_plan=is_default)
            await update.callback_query.edit_message_text(text="ست شد")

        case CD.API_STATS:
            keyboard = InlineKeyboardMarkup(Keyboards.BACK_TO_STATS)
            await update.callback_query.edit_message_text(text = await get_API_statistics(), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        case CD.STATISTICS:
            keyboard = InlineKeyboardMarkup(Keyboards.STATS_KEYBOARD)
            await update.callback_query.edit_message_text(text= await get_statistics(), reply_markup=keyboard)
        case CD.REFERRAL_STATISTICS:
            keyboard = InlineKeyboardMarkup(Keyboards.BACK_TO_STATS)
            await update.callback_query.edit_message_text(text= await get_referral_statistics(), reply_markup=keyboard)
        case CD.API_HEALTH_STATS:
            keyboard = InlineKeyboardMarkup(Keyboards.BACK_TO_STATS)
            await update.callback_query.edit_message_text(text= await get_API_health_statistics(), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
        case CD.REQUEST_TYPE_STATS:
            keyboard = InlineKeyboardMarkup(Keyboards.BACK_TO_STATS)
            await update.callback_query.edit_message_text(text= await get_request_type_statistics(), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
        case CD.STATS_CHARTS:
            dates = list(range(-30,1))
            query = User.all()
            users_joined = await get_stats_by_creation_time(query, 31)
            users_joined.reverse()
            import io
            import matplotlib.pyplot as plt
            # Create the line chart.
            plt.figure(figsize=(10, 6))
            plt.plot(dates, users_joined, marker='o', linestyle='-')
            plt.xlabel('Date')
            plt.ylabel('Number of New Users')
            plt.title('Users Joined Over Time')
            plt.grid(True)

            # Save the chart to an in-memory bytes buffer.
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)  # Rewind the buffer to the beginning.
            plt.close()  # Close the plot to free up memory.

            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buf)
        # Log or handle the case where the query is already too old.
        # logger.warning("Could not answer callback query: %s", e)
        case CD.LOYALTY_STATS:
            keyboard = InlineKeyboardMarkup(Keyboards.BACK_TO_STATS)
            await update.callback_query.edit_message_text(text= await get_loyalty_statistics(), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
        case CD.ADDING_NEW_MESSAGE:

            await context.bot.send_message(chat_id=user.id, text= "لطفا پیام خود را ارسال کنید")
            return CONV.GETTING_A_NEW_MESSAGE
        
        

        case CD.LISTING_MESSAGES:
            

            messages = await Message.all().limit(5).order_by('-created_at')
            if not messages:
                return await context.bot.send_message(chat_id=user.id, text= "no message in database")

            keyboard = []
            for message in messages:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{message.id} ID:", 
                            callback_data= CD.DO_NOTHING
                            ),
                        InlineKeyboardButton(
                            text= "نمایش",
                            callback_data= querify(CD.SHOW_DB_MESSAGE, message.id)
                        )
                        ])

            pm = "لیست پیام ها"
            
            return await context.bot.send_message(
                chat_id=user.id, 
                text= pm, 
                reply_markup= InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML)
        

        
        case CD.LISTING_SOURCE_LINKS:
            

            sources = await Source.all().limit(5).order_by('-created_at')\
                .annotate(
                    clicks_count=Count("clicks"),
                    unique_clicks_count=Count("clicks__user_id", distinct=True))
            if not sources:
                return await context.bot.send_message(chat_id=user.id, text= "no source in database")


            pm = "🗂Source list:\n\n\n"
            for source in sources:
                # print(source.__dict__)
                link = helpers.create_deep_linked_url(context.bot.username, Config.SOURCE_DEEP_LINK_PREFIX + source.identifier)
                
                # await source.fetch_related("clicks__user")
                # clicker_users = [click.user.id for click in source.clicks]
                # # unique_user_ids = await source.clicks.distinct("user_id").values_list("user_id", flat=True)
                # unique_clicks = len(set(clicker_users))

                # clicks = await Source.filter(id=source.id).annotate(count=Count("clicks", distinct=True)).values("count")
                # print(clicks)

                # clicks = clicks[0]['count']
                # unique_clicks = await Source.filter(id=source.id).annotate(count=Count("clicks__user_id", distinct=True)).values("count")
                # print(unique_clicks)

                # unique_clicks = unique_clicks[0]['count']

                pm+= f" ID: [<code>{source.id}</code>] (C: {source.clicks_count} | unique: {source.unique_clicks_count}) \n {link} \n\n"
            
            return await context.bot.send_message(chat_id=user.id, text= pm, parse_mode=ParseMode.HTML)
        
        case CD.ADDING_NEW_SOURCE_LINK:
            

            source = Source()
            await source.save()

            link = helpers.create_deep_linked_url(context.bot.username, Config.SOURCE_DEEP_LINK_PREFIX + source.identifier)
            pm= f" ID: [<code>{source.id}</code>] \n {link}"
            
            return await context.bot.send_message(chat_id=user.id, text= pm, parse_mode=ParseMode.HTML)
        
        case CD.ADD_NEW_BROADCAST:

            message = "لطفا پیام مد نظر خود را انتخاب کنید"

            db_messages = await Message.all().limit(10).order_by("-created_at")

            if not db_messages:
                return await update.callback_query.edit_message_text(
                    text="در حال حاضر هیچ پیامی برای ارسال همگانی تنظیم نشده است لطفا یک پیام تنظیم کنیم",
                    reply_markup=ReplyKeyboardMarkup([[BTN.AS_MESSAGE_MANAGEMENT]])
                    )

            keyboard = []
            for db_message in db_messages:
                keyboard.append([InlineKeyboardButton(
                    text=db_message.text if len(db_message.text)>30 else db_message.text[:30],
                    callback_data= querify(CD.SET_BROADCAST_MESSAGE, db_message.id)
                    )])

            if not keyboard:
                await update.callback_query.edit_message_text("پیامی برای ارسال همگانی وجود ندارد")
                return

            await update.callback_query.edit_message_text(text=message, reply_markup= InlineKeyboardMarkup(keyboard))

            return CONV.CHOOSE_MESSAGE_ID
        case CD.SET_BROADCAST_MESSAGE:

            context.user_data["bc_message_id"] = query[1]

            NUMBERS = [150, 300, 500, 1000, 1500]
            TEXTS = [
                "خیلی کند | {} عدد بر دقیقه",
                "کند | {} عدد بر دقیقه",
                "متوسط | {} عدد بر دقیقه",
                "نرمال | {} عدد بر دقیقه",
                "سریع | {} عدد بر دقیقه",
            ]
            keyboard = []
            for n, text in enumerate(TEXTS, 0):
                number_per_second = int(round(NUMBERS[n] / 60))
                keyboard.append([
                    InlineKeyboardButton(
                        text=text.format(NUMBERS[n]), 
                        callback_data=querify(CD.SET_BROADCAST_RATE, number_per_second)
                        )
                    ])
            await update.callback_query.edit_message_text(
                text= "سرعت ارسال را انتخاب کنید",
                reply_markup= InlineKeyboardMarkup(keyboard)
            )
        
        case CD.SET_BROADCAST_RATE:
            
            context.user_data["bc_rate"] = int(query[1])

            percentages = [1, 2, 5, 20, 50, 80, 100]

            keyboard = []
            for percentage in percentages:
                keyboard.append([
                    InlineKeyboardButton(
                        text=f" {percentage}%", 
                        callback_data=querify(CD.SET_BROADCAST_COVERAGE, percentage)
                        )
                    ])
            await update.callback_query.edit_message_text(
                text= "این پیغام همگانی به چند درصد اعضا ارسال شود؟",
                reply_markup= InlineKeyboardMarkup(keyboard)
            )

        case CD.SET_BROADCAST_COVERAGE:

            coverage_percentage = int(query[1])
            user_count = await User.filter(has_started = True, has_blocked_the_bot = False).count()
            number_of_users_to_be_sent_to = round(user_count *(coverage_percentage/100))

            broadcast = BroadCastRequest()
            broadcast.message_id = context.user_data["bc_message_id"]
            broadcast.messages_per_second = context.user_data["bc_rate"]
            broadcast.n_of_users_to_be_sent_to = number_of_users_to_be_sent_to
            await broadcast.save()

            await update.callback_query.edit_message_text("ارسال همگانی شما با موفقیت ایجاد شد")


        case CD.LIST_BROADCASTS:

            broadcasts = await BroadCastRequest.all().limit(10)
            keyboard = []
            for bc in broadcasts:
                state = "🔝" if bc.is_underway else "✅" if bc.is_finished else "⏸️"

                keyboard.append([
                    InlineKeyboardButton(
                        text= f"ID: {bc.id} | {state}",
                        callback_data= querify(CD.BROADCAST_INFO, bc.id)
                    )
                ])

            await update.callback_query.edit_message_text(
                text= Messages.LIST_OF_BROADCASTS, 
                reply_markup= InlineKeyboardMarkup(keyboard)
            )

        case CD.BROADCAST_INFO:
            broadcast_id = query[1]
            bc = await BroadCastRequest.filter(id=broadcast_id).first()

            msg = Messages.BROADCAST_INFO.format(
                bc.id,
                bc.messages_per_second * 60,
                bc.n_of_successfully_sent_messages,
                bc.n_of_users_already_covered,
                bc.n_of_users_to_be_sent_to,
                "🟩" if bc.is_underway else "🟥",
                "🟩" if bc.is_finished else "🟥",
            )

            toggle_btn = "🟥 توقف ارسال همگانی" if bc.is_underway else "🟩 شروع ارسال همگانی"

            
            keyboard = [
                [
                    InlineKeyboardButton(
                        text= "دیدن پیام",
                        callback_data= querify(CD.SHOW_BROADCAST_MESSAGE, bc.id)
                    )
                ]
            ]
            if not bc.is_finished:
                keyboard[0].append(InlineKeyboardButton(
                            text= toggle_btn,
                            callback_data= querify(CD.TOGGLE_BROADCASTING, bc.id)
                        ))
            await update.callback_query.edit_message_text(
                text= msg,
                reply_markup= InlineKeyboardMarkup(keyboard)
            )
        
        case CD.TOGGLE_BROADCASTING: # start(resume)/pause(stop)
            
            broadcast_id = query[1]
            bc = await BroadCastRequest.filter(id=broadcast_id).first()
            bc.is_underway = not bc.is_underway
            await bc.save()

            action = "فعال" if bc.is_underway else "غیرفعال"
            await update.callback_query.edit_message_text(
                text= f"ارسال همگانی {action} شد",
            )

            if bc.is_underway:
                await update.effective_chat.send_message(
                    text= f"ارسال همگانی شروع شد!! میتوانید میزان پیشرفت را از بخش اطلاعات ارسال همگانی مشاهده کنید یا آن را متوقف کنید."
                )
                # context.application.create_task(broadcast_message(
                #     context=context,
                #     broadcast_id=broadcast_id,
                #     chunk_size= 100
                # ))
                task = running_broadcasts.get(broadcast_id)
                if task and not task.done():
                    # A task is already running; optionally notify admin
                    await update.effective_chat.send_message(f"Broadcast {broadcast_id} is already running.")
                else:
                    # Create a new task and store it in the registry
                    task = context.application.create_task(broadcast_message(
                        context=context,
                        broadcast_id=broadcast_id,
                        chunk_size=100
                    ))
                    running_broadcasts[broadcast_id] = task

                    # Optionally, add a callback to remove the task from the registry once done
                    def task_done_callback(task: asyncio.Task):
                        running_broadcasts.pop(broadcast_id, None)
                        context.application.create_task(update.effective_chat.send_message(
                            text=f"ارسال همگانی {broadcast_id} تمام شد",
                        ))
                    task.add_done_callback(task_done_callback)
                # await broadcast_message(
                #     context=context,
                #     broadcast_id=broadcast_id,
                #     chunk_size= 100
                # )

        case CD.SHOW_BROADCAST_MESSAGE:
            
            broadcast_id = query[1]
            bc = await BroadCastRequest.filter(id=broadcast_id).prefetch_related('message').first()

            await send_a_db_message(
                context=context,
                chat_id=user.id,
                db_msg= bc.message
            )

        case CD.ADDING_NEW_COMMAND:

            await update.callback_query.edit_message_text("اسم دستور مد نظر رو بدون / بفرست. مثلا: help")
            return CONV.GETTING_A_NEW_COMMAND

        case CD.LISTING_COMMANDS:
            
            commands = await DynamicCommand.all().limit(5).order_by('-created_at')
            if not commands:
                return await context.bot.send_message(chat_id=user.id, text= "no commands in database")

            pm = "🗂Commands list:\n\n\n"

            keyboard = []

            for command in commands:
                keyboard.append(
                    [InlineKeyboardButton(
                        text=command.command_name, 
                        callback_data=querify(CD.COMMAND_INFO, command.id)
                        )]
                )
            
            return await context.bot.send_message(
                chat_id=user.id, 
                text= pm, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML)

        case CD.COMMAND_INFO:

            command_id = query[1]
            command = await DynamicCommand.filter(id=command_id).first().prefetch_related('messages')

            pm = f"""name: {command.command_name} \n پیام ها: {len(command.messages)} \nبا دکمه های زیر این دستور را ویرایش کنید"""
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="پیام ها", 
                        callback_data=querify(CD.COMMAND_MESSAGES_MANAGEMENT, command.id)
                        ),
                    InlineKeyboardButton(
                        text= "❌ حذف",
                        callback_data= querify(CD.DELETE_COMMAND, command.id)
                    )
                ]
            ]

            await update.callback_query.edit_message_text(text=pm, reply_markup=InlineKeyboardMarkup(keyboard))
        
        case CD.DELETE_COMMAND:

            command_id = query[1]
            command = await DynamicCommand.filter(id=command_id).delete()

            await update.callback_query.edit_message_text("دستور با موفقیت حذف شد")

        case CD.COMMAND_MESSAGES_MANAGEMENT:
            
            command_id = query[1]
            command = await DynamicCommand.filter(id=command_id).first().prefetch_related('messages')
            
            pm = "لیست پیام های این دستور"
            keyboard = []

            for message in command.messages:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{message.id} ❌", 
                            callback_data= querify(CD.DELETE_COMMAND_MESSAGE, command_id, message.id)
                            ),
                        InlineKeyboardButton(
                            text= "نمایش",
                            callback_data= querify(CD.SHOW_DB_MESSAGE, message.id)
                        )
                        ])
            keyboard.append([InlineKeyboardButton(
                text= "➕ افزودن پیام جدید",
                callback_data= querify(CD.ADD_COMMAND_MESSAGE, command_id)
            )])

            await update.callback_query.edit_message_text(
                text= pm, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        case CD.DELETE_COMMAND_MESSAGE:

            command_id = query[1]
            message_id = query[2]

            command = await DynamicCommand.filter(id=command_id).first().prefetch_related('messages')
            message = await Message.filter(id=message_id).first()
            await command.messages.remove(message)

            await update.callback_query.edit_message_text("پیام مد نظر از پیام های دستور حذف شد")
            
        case CD.SHOW_DB_MESSAGE:
            message_id = query[1]
            msg = await Message.filter(id = message_id).first()
            
            await send_a_db_message(
                context=context,
                chat_id=update.effective_chat.id,
                db_msg= msg
            )

        case CD.ADD_COMMAND_MESSAGE:
            command_id = query[1]

            messages = await Message.all().limit(5).order_by('-created_at')
            
            print(messages)
            if not messages:
                return await update.callback_query.edit_message_text("پیامی در دیتابیس وجود نداشت")

            pm = "پیامی که میخواهید به دستور اضاف شود را انتخاب کنید"
            keyboard = []

            for message in messages:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{message.id} ➕", 
                            callback_data= querify(CD.ADD_COMMAND_MESSAGE_TO_DB, command_id, message.id)
                            ),
                        InlineKeyboardButton(
                            text= "نمایش",
                            callback_data= querify(CD.SHOW_DB_MESSAGE, message.id)
                        )
                        ])
            
            await update.callback_query.edit_message_text(
                text= pm,
                reply_markup = InlineKeyboardMarkup(keyboard)
            )
        case CD.ADD_COMMAND_MESSAGE_TO_DB:
            command_id = query[1]
            message_id = query[2]

            command = await DynamicCommand.filter(id=command_id).first().prefetch_related('messages')
            message = await Message.filter(id=message_id).first()
            await command.messages.add(message)

            await update.callback_query.edit_message_text("پیام مد نظر به پیام های دستور اضافه شد")


        case CD.CHANNEL_DELETE:
            channel_id = query[1]
            channel = await Channel.filter(id = channel_id).first()

            message = Messages.ARE_YOU_SURE_YOU_WANNA_DELETE_CHANNEL.format(channel.title)

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    text= "بله مطمئنم",
                    callback_data=querify(CD.CHANNEL_DELETE_CONFIRMED, channel_id)
                )]]
            )

            await update.callback_query.edit_message_text(
                text= message,
                reply_markup= keyboard
            )
        
        case CD.CHANNEL_DELETE_CONFIRMED:
            channel_id = query[1]
            channel = await Channel.filter(id = channel_id).delete()

            await context.bot.leave_chat(chat_id=channel_id)

            await update.callback_query.edit_message_text(
                text= "چنل با موفقیت حذف شد!"
            )

        case CD.CHANNEL_INFO:

            channel_id = query[1]
            channel = await Channel.filter(id = channel_id).first().prefetch_related('acceptor_message')

            if not channel:
                await update.callback_query.edit_message_text("چنین کانالی وجود ندارد")

            tracking_state = "✅" if channel.is_chatmember_tracking_active else "❌"
            channel_info = Messages.CHANNEL_INFO.format(
                channel.title,
                channel.id,
                channel.admin_id,
                tracking_state
            )

            has_acceptor_message = "✅" if channel.acceptor_message else "❌"
            print(has_acceptor_message)

            keyboard = [
                [
                    InlineKeyboardButton(
                        text= f"{tracking_state} پیگیری", 
                        callback_data = querify(CD.CHANNEL_TOGGLE_TRACKING, channel_id)
                        ),
                    InlineKeyboardButton(
                        text = "تنظیم پیام اکسپتر",
                        callback_data = querify(CD.CHANNEL_ACCEPTER_MESSAGE_MANAGEMENT, channel_id)
                    ),
                    
                ],
                [
                    InlineKeyboardButton(
                        text = "نمایش پیام اکسپتر فعلی" + has_acceptor_message,
                        callback_data = querify(CD.SHOW_DB_MESSAGE, channel.acceptor_message.id) if channel.acceptor_message 
                        else CD.DO_NOTHING
                    )
                ]
            ]
            await update.callback_query.edit_message_text(
                text= channel_info,
                reply_markup= InlineKeyboardMarkup(keyboard)
            )

        case CD.CHANNEL_TOGGLE_TRACKING:
            channel_id = query[1]
            channel = await Channel.filter(id = channel_id).first()

            channel.is_chatmember_tracking_active = not channel.is_chatmember_tracking_active
            await channel.save()

            tracking_state = "✅ فعال" if channel.is_chatmember_tracking_active else "❌ غیرفعال"

            await update.callback_query.edit_message_text(
                text= f"پیگیری اعضا با موفقیت {tracking_state} شد"
            )

        case CD.CHANNEL_ACCEPTER_MESSAGE_MANAGEMENT:

            channel_id = query[1]
            messages = await Message.all().limit(5).order_by('-created_at')
            
            if not messages:
                return await update.callback_query.edit_message_text("پیامی در دیتابیس وجود نداشت")

            pm = "پیامی که میخواهید به عنوان پیام اکسپتر شود را انتخاب کنید"
            keyboard = []

            for message in messages:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{message.id} ➕", 
                            callback_data= querify(CD.CHANNEL_SET_ACCEPTER_MSG, channel_id, message.id)
                            ),
                        InlineKeyboardButton(
                            text= "نمایش",
                            callback_data= querify(CD.SHOW_DB_MESSAGE, message.id)
                        )
                        ])
            
            await update.callback_query.edit_message_text(
                text= pm,
                reply_markup = InlineKeyboardMarkup(keyboard)
            )
            
        case CD.CHANNEL_SET_ACCEPTER_MSG:

            channel_id = query[1]
            message_id = query[2]

            channel = await Channel.filter(id = channel_id).first()
            channel.acceptor_message_id = message_id
            await channel.save()



            await update.callback_query.edit_message_text("تنظیم پیام انجام شد")

        case CD.NEW_BTN:
            message_id = query[1]
            row_number = query[2]
            

            await update.callback_query.edit_message_text("عنوان دکمه رو ارسال کن")
            context.user_data['add_btn'] = [message_id, row_number]

            return CONV.SET_BTN_TITLE

        case CD.CHOOSE_BTN_TYPE:
            
            pass
            


        case CD.CHOOSE_BTN_MESSAGE:
            msg_sent_when_btn_is_clicked = query[1]
            message_id, row_number, btn_text = context.user_data['add_btn']
            
            context.user_data.clear()

            await create_btn(
                context= context,
                update= update,
                message_id= message_id,
                row_number=row_number,
                btn_text= btn_text,
                btn_type= "msg",
                extra_info= msg_sent_when_btn_is_clicked
            )
            # msg = await Message.filter(id = message_id).first()
            
            # new_btn = {
            #             "text": btn_text,
            #             "callback_data": querify(CD.SHOW_DB_MESSAGE, msg_sent_when_btn_is_clicked)
            #             }
            # if row_number == "N":
            #     msg.keyboard.append([new_btn])
            # else:
            #     msg.keyboard[int(row_number)].append(new_btn)

            # await msg.save()

            # await send_a_db_message(
            #     context=context,
            #     chat_id= update.effective_chat.id,
            #     db_msg= msg
            # )

        
        case CD.ADD_CHANNEL:
            
            await update.callback_query.edit_message_text(
                text= "یه پیام از اون چنل فوروارد کن"
            )
            
            return CONV.GET_CHANNEL_MSG
        

        case CD.INCREASE_BALANCE:

            msg = Messages.BALANCE_MANAGING_TIPS.format(
                Config.TRANSACTION_AMOUNTS.INSTAGRAM_REQUEST_COINS,
                Config.TRANSACTION_AMOUNTS.REFERRAL_GIFT,
                Config.TRANSACTION_AMOUNTS.LOYALTY_GIFT_COINS,
                Config.CURRENCY_TYPES.GEM_TO_COIN_RATIO
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        text= "🔗 دریافت لینک زیرمجموعه گیری",
                        callback_data= CD.GET_REFERRAL_LINK
                    )
                ]
            ]

            await update.callback_query.edit_message_text(
                text=msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        case CD.GET_REFERRAL_LINK:

            
            link = helpers.create_deep_linked_url(context.bot.username, Config.REFERRAL_DEEP_LINK_PREFIX + str(update.effective_user.id))
            await update.callback_query.edit_message_text(
                f"لینک زیرمجموعه گیری شما آماده است: \n{link}\nمی توانید لینک بالا یا پیام پایین را به فرد مد نظر ارسال کنید."
            )

            await update.effective_chat.send_message(
                f"""🧐 شنیدم تو هم دوست داری بتونی راحت ریلز ها، پست ها، عکس پروفایل کاربرا یا هایلایتاشون رو از اینستاگرام دانلود کنی
😜 یا میخوای استوری پیجای دیگه رو دانلود کنی بدون اینکه سین بزنی!

<a href='{link}'>👆 🔻 کافیه [اینجا] کلیک کنی تا بتونی راحت این کارو انجام بدی 🔻</a>
""",

parse_mode=ParseMode.HTML)
            

