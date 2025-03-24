
import json
from typing import Any, List
from pydantic import BaseModel, TypeAdapter

from telegram import Message, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from config import Config
from db.models import APIReq, InstagramAccount, InstagramRequest, Transactions, UserBalance
from handlers.constants.callback_data import CD
from handlers.constants.messages import Messages
from handlers.constants.buttons import BTN
from handlers.utils.downloader_utils import (
    complies_with_cache_policies, 
    get_fastsaverapi_req_object, 
    get_insta_scraper_api_req_object, 
    get_instagram_user_id_by_username, 
    get_instagram_username_by_id, 
    get_one_api_req_object, 
    # send_media, 
    send_user_highlights
    )
from handlers.utils.send_media import send_media
from handlers.utils.user_info import UserFunctionalities
from handlers.utils.utils import decrease_or_send_no_balance_message, give_them_loyalty_gift, needs_force_join, number_to_telegram_emojis, querify, dequierify, extract_instagram_link_type_and_id, report_in_channel
from handlers.utils.pydanticmodels import FastServerAPIResultForPostsAndStories, Highlight, InstaScraperSuccessResponse, InstagramScraperResponse, InstagramScraperUserData, Story, OneAPIResponse, InstaUserProfile, InstagramPost, MediaItem
from handlers.utils.one_api import API_STATUS_CODES, InstagramAPI, InstagramFastSaverAPI, InstagramScraperAPI
# from db.models import Group, User, Message

import logging

from handlers.utils.pydantic_models.instagram_scraper import InstagramScraperPost, convert_list_of_media_data_to_media_version, get_media_list_for_post_reel, get_media_list_for_story

import sys
import logging


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@give_them_loyalty_gift
@needs_force_join
async def instagram_downloader(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    if_callback_query = False, 
    download_info = (),
    remaining_api_providers: None | tuple = None,
    wait_message: None | Message = None,
    tries = 0,
    ):


    user_functionalities:UserFunctionalities = context.user_data['user_functionalities']

    tries +=1

    if tries > 3:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= """⚠️ دانلود ناموفق بود!
🔗 لطفاً بررسی کنید که لینک صحیح است و دوباره تلاش کنید. 🔄"""
        )

    share_in_url = False

    if not if_callback_query:
        if update.message.text.startswith("@"):
            link = Config.INSTAGRAM_BASE_URL+update.message.text[1:]
        else:
            link = update.message.text
        
        link = link.strip()
        print(link)

        link_info = extract_instagram_link_type_and_id(link)

        if link_info == None:
            context.application.create_task(report_in_channel(
                context=context, 
                text= f"❌ user message was not identified as a valid instagram link using extract_instagram_link_type_and_id: \n\n{link}"
                ))
            

            return await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text= """❌ خطا در تحلیل لینک

◀️ کاربر عزیز لطفا لینک پست، ریلز، استوری یا پروفایل کاربر را به صورت مستقیم و تنها بدون متن اضافه در یک پیام ارسال کنید."""
                )

        type_of_request = link_info[0]
        
        
        if type_of_request == "share":
            share_in_url=True
            type_of_request= Config.INSTAGRAM_REUQEST_TYPES.POST if link_info[1]=="p" else link_info[1]

        params = link_info[1:]

        # because fast saver api does not support /s/ links-> converting the link to stories/highlights/
        if type_of_request == Config.INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES:
            base_link:str = Config.INSTAGRAM_BASE_URL_PATTERNS.get(type_of_request)
            link = base_link.format(params[0])
        

        # making links like this compatible for fastsaver api :
        # https://www.instagram.com/parvanekarami32/reel/DGeQzAvNNBL
        if type_of_request in (Config.INSTAGRAM_REUQEST_TYPES.REEL, Config.INSTAGRAM_REUQEST_TYPES.POST) and not share_in_url:
            base_link:str = Config.INSTAGRAM_BASE_URL_PATTERNS.get(type_of_request)
            link = base_link.format(params[0])
        
        if type_of_request == Config.INSTAGRAM_REUQEST_TYPES.STORY:
            
            print(params)
            story_username = params[0]
            story_id = params[1]
            message = "کل استوری های این اکانتو دانلود کنم یا فقط همین استوری؟🧐"
            keyboard = [
                [
                    InlineKeyboardButton(text="دانلود همین استوری", callback_data=querify(CD.DL_SINGLE_STORY, story_username, story_id)),
                    InlineKeyboardButton(text="دانلود همش", callback_data=querify(CD.DL_STORIES, story_username))
                ]
            ]

            return await update.effective_chat.send_message(text=message, reply_markup=InlineKeyboardMarkup(keyboard))
        
            
    else:
        type_of_request = download_info[0]
        params = download_info[1:]

        print('dl info', download_info)
        base_link:str = Config.INSTAGRAM_BASE_URL_PATTERNS.get(type_of_request)

        

        if type_of_request in (
            Config.INSTAGRAM_REUQEST_TYPES.STORIES, 
            Config.INSTAGRAM_REUQEST_TYPES.STORY
            ):
            def is_convertible_to_int(s):
                try:
                    int(s)
                    return True
                except ValueError:
                    return False

            username = params[0] if not is_convertible_to_int(params[0]) else await get_instagram_username_by_id(params[0])
            
            if type_of_request == Config.INSTAGRAM_REUQEST_TYPES.STORY:
                link = base_link.format(username, params[1])
            else:
                link = base_link.format(username)
        
        else:
            link = base_link.format(params[0])
        
    if type_of_request == Config.INSTAGRAM_REUQEST_TYPES.AUDIO:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= """🚫 متأسفانه امکان دانلود آهنگ ریلز‌ها فعال نیست.
⏳ این قابلیت تا چند روز آینده به ربات اضافه خواهد شد. 🙌🎵"""
            )
    # elif type_of_request == Config.INSTAGRAM_REUQEST_TYPES.STORY:
    
    #     return await context.bot.send_message(
    #         chat_id=update.effective_chat.id,
    #         text= 
    #         )
    # print(download_info)

    if not Config.IN_PRODUCTION:
        info = download_info if download_info else link_info
        logger.info(msg = f"RT:{type_of_request} | {link} | {str(info)}")
        # print(type_of_request, share_in_url)
        # print(link_info)

            

    # if not does_user_have_permission_to_do_this(context=context, request_type=type_of_request):
    #     return await context.bot.send_message(
    #         chat_id=update.effective_chat.id, 
    #         text= "کاربر عزیز شما امکان دریافت این نوع درخواست را ندارید"
    #         )
    
    
    # rate_limit_passed, time_till_next_request = await rate_limit_info(context)
    # if rate_limit_passed:
    #     return await context.bot.send_message(
    #         chat_id= update.effective_chat.id,
    #         text="lotfan {} sanie ta darkhast badi sabr konid".format(time_till_next_request)
    #         )

    # insta_API = InstagramAPI(Config.ONE_API_TOKEN)
    # api_provider = Config.SERVICE_PROVIDERS.ONEAPI


    # remaining_api_providers = None | [api1, api2] | []
    if remaining_api_providers is None:
    # First call (no recursion), initialize the provider list
        if share_in_url:
            remaining_api_providers = Config.PREFERED_SERVICE_PROVIDERS.get("share")
        else:
            remaining_api_providers = Config.PREFERED_SERVICE_PROVIDERS.get(type_of_request)
        
        # Pop the first provider from the list
        api_provider = remaining_api_providers[0]
        remaining_api_providers = remaining_api_providers[1:]
    else:
        # Recursive call (previous API provider failed)
        if not remaining_api_providers:
            # No providers left to try
            return await wait_message.edit_text(
                text="""⚠️ دانلود ناموفق بود!
🔗 لطفاً بررسی کنید که لینک [صحیح باشد] و اکانت مد نظر [پرایوت نباشد] و دوباره تلاش کنید. 🔄

◀️ ممکن است موقتا اینستاگرام امکان دانلود این لینک را بسته باشد
""")
        else:
            # Providers remain, so try the next one
            api_provider = remaining_api_providers[0]
            remaining_api_providers = remaining_api_providers[1:]

    # api_provider = Config.SERVICE_PROVIDERS.ONEAPI

    match api_provider:
        case Config.SERVICE_PROVIDERS.ONEAPI:
            api_req = await get_one_api_req_object(type_of_request, params, link, share_in_url)
        case Config.SERVICE_PROVIDERS.FASTSAVERAPI:
            api_req = await get_fastsaverapi_req_object(link=link)
        case Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
            api_req = await get_insta_scraper_api_req_object(type_of_request, params, link)
    

    similar_request_in_db = await InstagramRequest.filter(
            request_status = InstagramAPI.REQUEST_STATUS.SUCCESS,
            request_type = type_of_request,
            parameters = api_req.parameters
        ).order_by("-created_at").first()
    
    if not wait_message:
        wait_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>📡 در حال اتصال به اینستاگرام. . .</b>", 
                parse_mode=ParseMode.HTML)
    else:
        await wait_message.edit_text(
                text=f"<b>📡 در حال اتصال به اینستاگرام. . .</b> [{tries}/3]", 
                parse_mode=ParseMode.HTML)

    is_cached = False

    if similar_request_in_db and Config.CACHE_ACTIVE:
        await similar_request_in_db.fetch_related("api_request")
        compliance_with_cache_policies = complies_with_cache_policies(
            request_type=type_of_request,
            saved_at= similar_request_in_db.api_request.created_at
        )
        if compliance_with_cache_policies:
            is_cached=True
            if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                result = InstagramScraperResponse(**similar_request_in_db.api_request.response)
            else:
                result = OneAPIResponse(**similar_request_in_db.api_request.response)

            api_req_in_db = similar_request_in_db.api_request
    
    if not is_cached:
        try:
            # apply the timeout logic here
            result = await api_req.fetch()
        except Exception as e:
            await wait_message.edit_text(text="با خطایی در دانلود مواجه شدیم. در حال امتحان روش دیگری هستیم لطفا صبور باشید")

            error_message = f"❌ error in fetching!: [{api_provider}]\n {str(e)}"
            context.application.create_task(report_in_channel(context=context, text= error_message))
            #>>>>>> here you shoud add failed api message to the database to monitor the successfulness of apis 
            return await instagram_downloader(
                update=update,
                context=context,
                if_callback_query=if_callback_query,
                download_info=download_info,
                remaining_api_providers=remaining_api_providers,
                wait_message=wait_message,
                tries=tries
            )


    
        
        
        # logger.info(msg=str(json.dumps(result.model_dump_json(), indent=4)))
        # print(f"{api_provider} : {result}")
            
        API_request = APIReq()
        API_request.url = api_req.api_request_url
        API_request.parameters = api_req.parameters
        API_request.status = result.status
        API_request.response = result.model_dump_json()
        API_request.service_provider = api_provider
        await API_request.save()

        api_req_in_db = API_request

    if result.status != API_STATUS_CODES.SUCCESS:
            go_to_next_api_provider = False

            if type_of_request == Config.INSTAGRAM_REUQEST_TYPES.STORIES:
                x = "2️⃣ کاربر مورد نظر استوری فعالی ندارد" + "\n"
            else:
                x= "2️⃣ لینک ارسالی اشتباه است.\n"
            error_message_for_user = f"""🔍 <b>خطا در پردازش لینک ارسالی شما</b>\n\n
❌ <b>دلایل ممکن:</b>\n
1️⃣ اکانت موردنظر خصوصی (پرایوت) است.\n
{x}
3️⃣ اینستاگرام در حال حاضر اجازه دانلود این محتوا را نمی‌دهد.\n\n
🔄 <b>لطفاً بررسی کنید و دوباره تلاش کنید.</b> 🙏"""
            
            status_code = number_to_telegram_emojis(result.status)
            error_message_for_admin = f"{status_code} | {api_provider} \n 🔗 {link}: \n\n {result.model_dump_json()} "
            
            match result.status:
                case API_STATUS_CODES.BAD_REQUEST:
                    go_to_next_api_provider = False

                    if (api_provider == Config.SERVICE_PROVIDERS.FASTSAVERAPI) and \
                        type_of_request in (Config.INSTAGRAM_REUQEST_TYPES.POST, Config.INSTAGRAM_REUQEST_TYPES.REEL): # invalid url
                        # >>>>>> go to next service provider or retry(if tries == 1)
                        error_message_for_user = "❌ دانلود ناموفق بود! در حال تلاش دوباره 🔄 "
                        go_to_next_api_provider = True # using instagram scraper because fastsaverapi is unreliable
                        
                         
                case API_STATUS_CODES.UNAUTHORIZED: # token is problematic
                    go_to_next_api_provider = False
                    error_message_for_admin = "❌❌ TOOOOOOOOKEN MOSHKEL DARE! \n" + error_message_for_admin
                    
                case API_STATUS_CODES.FORBIDDEN: # no money in one api

                    if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                        error_message_for_user = Messages.THE_ACCOUNT_IS_PRIVATE
                    elif api_provider == Config.SERVICE_PROVIDERS.ONEAPI:
                        error_message_for_admin = "❌❌ POOOOOOOOOOOOOL NADARI! SHARZH KON \n" + error_message_for_admin
                        
                    go_to_next_api_provider = False

                    
                    pass
                case API_STATUS_CODES.RESTRICTED_OR_REMOVED:
                    go_to_next_api_provider = False
                    pass
                case API_STATUS_CODES.PATH_DOESNT_EXIST:
                    go_to_next_api_provider = False
                    pass
                case API_STATUS_CODES.SERVER_ERROR:
                    go_to_next_api_provider = True
                case API_STATUS_CODES.API_COULDNT_DOWNLOAD_THIS:
                    go_to_next_api_provider = True

            context.application.create_task(report_in_channel(context=context, text=error_message_for_admin))

            if not go_to_next_api_provider:
                return await wait_message.edit_text(text=error_message_for_user, parse_mode=ParseMode.HTML)
            
            return await instagram_downloader(
                update=update,
                context=context,
                if_callback_query=if_callback_query,
                download_info=download_info,
                remaining_api_providers=remaining_api_providers,
                wait_message=wait_message,
                tries=tries
            )
    

    async def create_new_db_req():
        new_db_request = InstagramRequest()
        new_db_request.user = user_functionalities.db_user
        new_db_request.request_type = type_of_request
        new_db_request.request_status = result.status
        new_db_request.parameters = api_req.parameters
        new_db_request.api_request = api_req_in_db
        await new_db_request.save()
    context.application.create_task(create_new_db_req())
    
    await wait_message.edit_text(text = "🚀 <b>در حال ارسال ...</b>", parse_mode=ParseMode.HTML)    
    ## maybe we can define a function in ONEAPI that give us the request info instead of having to do it this way
    


    
    data_from_api = result.result
    
    # print(data_from_api)
    if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
        data_from_api=data_from_api.data

        
    match type_of_request:
        case (
            Config.INSTAGRAM_REUQEST_TYPES.POST | 
            Config.INSTAGRAM_REUQEST_TYPES.REEL | 
            Config.INSTAGRAM_REUQEST_TYPES.TV | 
            Config.INSTAGRAM_REUQEST_TYPES.JUST_SHARE):

            if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                post_or_reel = InstagramScraperPost(**data_from_api)

                print(post_or_reel)
            else:    
                #fast saver api or one api
                post_or_reel = InstagramPost(**data_from_api)

            
            message = Messages.HERES_YOUR_FILE.format(len(post_or_reel.media))
            await wait_message.edit_text(text=message)

            sent_msg = await send_media(
                update=update, 
                context=context, 
                media_list=post_or_reel.media, 
                caption=post_or_reel.caption,
                request_url = link)

        case Config.INSTAGRAM_REUQEST_TYPES.STORY:

            # the function get_media_list_for_story only works for instagram scraper api
            if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                media_list = get_media_list_for_story(data_from_api)
            elif api_provider == Config.SERVICE_PROVIDERS.FASTSAVERAPI:
                # print(data_from_api)
                try:
                    media_list = [MediaItem(**data_from_api)]
                except:
                    media_list = TypeAdapter(List[MediaItem]).validate_python(data_from_api['medias'])

            # print(media_list[0].model_dump_json())
            
            message = Messages.HERES_YOUR_STORY.format(1)
            await wait_message.edit_text(text=message)
            sent_msg = await send_media(
                update=update, 
                context=context, 
                media_list=media_list,
                request_url=link
                )

        case Config.INSTAGRAM_REUQEST_TYPES.STORIES:
            
            if api_provider == Config.SERVICE_PROVIDERS.ONEAPI:
                stories = TypeAdapter(List[MediaItem]).validate_python(data_from_api)
            elif api_provider == Config.SERVICE_PROVIDERS.FASTSAVERAPI:
                stories = FastServerAPIResultForPostsAndStories(**data_from_api).media
            elif api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                pass

            message = Messages.HERES_YOUR_STORIES.format(len(stories))
            await wait_message.edit_text(text=message)
            sent_msg = await send_media(
                update=update, 
                context=context, 
                media_list=stories,
                request_url= link)
            
        case Config.INSTAGRAM_REUQEST_TYPES.USER_INFO:
            if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                info = InstagramScraperUserData(**data_from_api)
                class user_data_class(BaseModel):
                    profile:str
                    profile_hd:str
                    id:int
                    username:str
                    full_name:str
                    bio:str|None = ""
                    type: Any = ""
                    posts:int|None = 0
                    followers:int
                    following:int
                    is_verified:bool
                    is_business:bool
                    
                
                user_data = user_data_class(
                    profile = info.profile_pic_url_hd,
                    profile_hd = info.profile_pic_url_hd,
                    id = info.id,
                    username = info.username,
                    full_name = info.full_name,
                    bio = info.biography,
                    type = "Private" if info.is_private else "Public",
                    posts = info.media_count,
                    followers = info.follower_count,
                    following = info.following_count,
                    is_verified = info.is_verified,
                    is_business = info.is_verified # I just did this to avoid problems
                )
                # user_data.profile_hd = 
                # user_data.id = 
                # user_data.username = info.username
                # user_data.full_name = info.full_name
                # user_data.bio = info.biography
                # user_data.type = "Private" if info.is_private else "Public"
                # user_data.posts = info.media_count
                # user_data.followers = info.follower_count
                # user_data.following = info.following_count
                # user_data.is_verified = info.is_verified
                # user_data.is_business = info.account_category

            else:
                user_data = InstaUserProfile(**data_from_api)

            message = (
                f"👤 Instagram Profile Info:\n"
                f"🔹 Username: {user_data.username}\n"
                f"📛 Full Name: {user_data.full_name or 'N/A'}\n"
                f"📜 Bio: {user_data.bio or 'N/A'}\n"
                f"🔍 Type: {user_data.type}\n"
                f"📝 Posts: {user_data.posts}\n"
                f"👥 Followers: {user_data.followers}\n"
                f"👤 Following: {user_data.following}\n"
                f"✅ Verified: {'Yes' if user_data.is_verified else 'No'}\n"
                f"🏢 Business Account: {'Yes' if user_data.is_business else 'No'}\n"
                # f"[🖼 Profile Picture]({user_data.profile})"
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="دانلود استوری ها", callback_data=querify(CD.DL_STORIES, user_data.id)), 
                    InlineKeyboardButton(text="لیست هایلایت ها", callback_data=querify(CD.HIGHLIGHS_LIST, user_data.id))
                 ],
                # [InlineKeyboardButton(text="عکس پروفایل HD", callback_data="gg")],
                ])
            
            escaped_caption = escape_markdown(message, version=2)

            sent_msg = await update.message.reply_photo(
                photo= user_data.profile_hd,
                caption=escaped_caption, 
                parse_mode=ParseMode.MARKDOWN_V2,
                # disable_web_page_preview=True, 
                reply_markup=keyboard
                )

            if not await InstagramAccount.get_or_none(id=user_data.id):
                await InstagramAccount.create(**user_data.model_dump())

            
        case Config.INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES:
            if api_provider == Config.SERVICE_PROVIDERS.ONEAPI:
                stories = TypeAdapter(List[MediaItem]).validate_python(data_from_api)
            else:
                stories = FastServerAPIResultForPostsAndStories(**data_from_api).media

            
            message = Messages.HERES_HIGHTLIGHT_STORIES.format(len(stories))
            await wait_message.edit_text(text=message)
            sent_msg = await send_media(
                update=update, 
                context=context, 
                media_list=stories, 
                request_url=link
                )
        
        case Config.INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS:
            if api_provider == Config.SERVICE_PROVIDERS.INSTASCRAPERAPI:
                data_from_api = data_from_api['items']

            await wait_message.delete()
            highlights = TypeAdapter(List[Highlight]).validate_python(data_from_api)
            sent_msg = await send_user_highlights(chat_id=update.effective_chat.id, context=context, highlights=highlights)
        # case Config.INSTAGRAM_REUQEST_TYPES.STORY:
        #     return

        # case Config.INSTAGRAM_REUQEST_TYPES.STORY:
        #     return

    # print(sent_msg)
    if isinstance(sent_msg, Message) or all(isinstance(item, Message) for item in sent_msg):
        # await wait_message.delete()     
        
        
        # await decrease_or_send_no_balance_message(
        #     context= context,
        #     currency_type= UserBalance.CURRENCY_TYPES.GOLD_COIN,
        #     reason= Config.TRANSACTION_REASONS.INSTAGRAM_DOWNLOAD,
        #     amount= Config.TRANSACTION_AMOUNTS.INSTAGRAM_REQUEST_COINS
        # )
        pass
    else:
        if sent_msg == Config.ERRORS.SENDING_MESSAGE.PROBLEMATIC_LINK_OR_INABILITY_TO_CHECK_SIZE:

            await wait_message.edit_text(
                text= "ارسال ناموفق بود! در حال تلاش دوباره..."
            )

            return await instagram_downloader(
                update=update,
                context=context,
                if_callback_query=if_callback_query,
                download_info=download_info,
                remaining_api_providers=remaining_api_providers,
                wait_message=wait_message,
                tries=tries
            )

        else:
            print(sent_msg)
            # if sent_msg == Config.ERRORS.SENDING_MESSAGE.FORBIDDEN:
            """>>>>>>>>>>>>>>>>>>use Config.error.... == sent_msg for checks and special messages for errors"""
            await wait_message.edit_text(text="""❌ در ارسال فایل درخواستی مشکلی پیش آمد

🔄 ممکن است اینستاگرام اجازه ارسال این فایل را در حال حاضر محدود کرده باشد. اگر از وجود فایل مد نظر و سالم بودن لینک ارسالی اطمینان دارید لطفا پس از کمی صبر از دوباره تلاش کنید.""")

# async def how_to_add_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

#     await update.message.reply_text(Messages.HOW_TO_ADD_A_GROUP)


# async def list_user_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.effective_user
#     chat = update.effective_chat
#     user_groups = await Group.filter(admin_id = user.id).all()

#     print(user_groups)
#     if not user_groups:
#         return await update.message.reply_text(Messages.NO_GROUPS)
#     keyboard = []
#     for group in user_groups:

#         icon_active = "✅" if group.is_comment_active else "❌"
#         icon_has_message = "✅" if await Message.filter(group_id = group.id).exists() else "❌"
#         keyboard.append([
#             InlineKeyboardButton(
#                 f"{icon_active} {group.title}", 
#                 callback_data=querify(
#                     BTN.CBD_GROUP_SETTING,
#                     group.id
#                 )),
#             InlineKeyboardButton(
#                 icon_has_message+BTN.SET_MESSAGE, 
#                 callback_data=querify(
#                     BTN.CBD_SETMESSAGE,
#                     group.id
#                 )),
#             InlineKeyboardButton(
#                 BTN.LEAVE_GROUP, 
#                 callback_data=querify(
#                     BTN.CBD_LEAVE_GROUP,
#                     group.id
#                 )),
#         ])
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text(Messages.LIST_OF_YOUR_GROUPS, reply_markup = reply_markup)

# async def new_post(update:Update, context:ContextTypes.DEFAULT_TYPE):

#     group = await Group.filter(id = update.effective_chat.id).first()
#     if not group:
#         return
#     if not group.is_comment_active:
#         await update.message.delete()
#     else:
#         message = await Message.get_or_none(group_id = group.id)

#         if message:
#             await update.message.reply_text(text=message.text)

# async def set_message(update:Update, context:ContextTypes.DEFAULT_TYPE):

#     group_id = dequierify(context.UDO.state)[1]
#     context.UDO.state = ''
#     await context.UDO.save()
#     message_exists = await Message.filter(group_id = group_id).exists()
    

#     if message_exists:
#         await Message.filter(group_id = group_id).update(text = update.message.text)
#     else:
#         await Message.create(text = update.message.text, group_id = group_id)

#     await update.message.reply_text(Messages.SUCCESSFULLY_SET_YOUR_GROUP_MESSAGE)

# async def delete_message(update:Update, context:ContextTypes.DEFAULT_TYPE):

#     group_id = dequierify(context.UDO.state)[1]
#     context.UDO.state = ''
#     await context.UDO.save()
#     await Message.filter(group_id = group_id).delete()
#     await update.message.reply_text(Messages.SUCCESSFULLY_DELETED_YOUR_GROUP_MESSAGE)

# async def add_admin(update:Update, context:ContextTypes.DEFAULT_TYPE):
#     await User.filter(id= update.effective_user.id).update(state = BTN.CBD_ADDING_ADMIN)
#     await update.message.reply_text(Messages.THIS_IS_HOW_TO_ADD_ADMIN)
    
# async def setting_new_admin_id(update:Update, context:ContextTypes.DEFAULT_TYPE):
    
#     await User.filter(id= update.effective_user.id).update(state = '')


#     user = update.message.forward_origin.sender_user
#     logger.info("%s added %s as admin", update.effective_user.full_name, user.full_name)
    
#     if await User.filter(id = user.id).exists():
        
#         await User.filter(id = user.id).update(role = User.SADEGH_ADMINS)
#     else:
#         dbuser = User()
#         dbuser.id = user.id
#         dbuser.first_name = user.first_name
#         dbuser.last_name = user.last_name if user.last_name else ''
#         dbuser.state = ''
#         dbuser.has_started = False
#         dbuser.role = User.SADEGH_ADMINS
#         await dbuser.save()
    
#     await update.message.reply_text(Messages.ADMIN_WAS_SUCCESSFULLY_ADDED)

# async def list_admins(update:Update, context:ContextTypes.DEFAULT_TYPE):

#     admins = await User.filter(role = User.SADEGH_ADMINS).all()
#     if not admins:
#         return await update.message.reply_text(Messages.YOU_HAVE_NO_ADMINS)

    
#     keyboard = []
#     for admin in admins:
#         keyboard.append([
#             InlineKeyboardButton(
#                 f"❌ {admin.first_name} {admin.last_name}", 
#                 callback_data=querify(
#                     BTN.CBD_REMOVE_ADMIN,
#                     admin.id
#                 )),
#         ])

#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text(Messages.THIS_IS_THE_LIST_OF_ADMINS, reply_markup=reply_markup)


async def this_bot_doesnt_support_edited_txts(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
    ):

    await update.effective_message.reply_text(
        text= """سلام 🙂👋
متاسفانه ربات قادر به پاسخگویی پیام های ویرایش شده نیست. لطفا متن ویرایش شده خود را در یک پیام جدید ارسال کنید🙏"""
    )

async def my_balance(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
    ):

    ufuncs:UserFunctionalities = context.user_data['user_functionalities']
    db_balance = ufuncs.balance_manager.db_balance

    balance_msg = """
🏦 مدیریت موجودی حساب شما

🥇 تعداد سکه: {}
💎 تعداد الماس: {}
""".format(db_balance.gold_coin, db_balance.gem)

    
    

    keyboard = [
        [
            InlineKeyboardButton(
                text= "افزایش موجودی ➕",
                callback_data= CD.INCREASE_BALANCE
            )
        ]
    ]

    await update.message.reply_text(
        text= balance_msg,
        reply_markup= InlineKeyboardMarkup(keyboard),
    )


async def referral_info(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
    ):

    balance_msg = """
👥 اطلاعات زیر مجموعه گیری

🧑🏻‍💼 تعداد زیرمجموعه ها: {}
🔗 شما به هر زیرمجموعه گیری {} سکه دریافت می کنید
"""
    ufuncs:UserFunctionalities = context.user_data['user_functionalities']

    db_balance = ufuncs.balance_manager.db_balance
    balance_msg = balance_msg.format(await ufuncs.referral_manager.get_referrals_count(), Config.TRANSACTION_AMOUNTS.REFERRAL_GIFT)

    keyboard = [
        [
            InlineKeyboardButton(
                text= "🔗 دریافت لینک زیرمجموعه گیری",
                callback_data= CD.GET_REFERRAL_LINK
            )
        ]
    ]

    await update.message.reply_text(
        text= balance_msg,
        reply_markup= InlineKeyboardMarkup(keyboard),
    )


