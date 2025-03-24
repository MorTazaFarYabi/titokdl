

import os
from typing import Tuple
import asyncio
import datetime
import aiohttp
from telegram.error import BadRequest, RetryAfter, Forbidden
from typing import List
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InputMediaAnimation, 
    InputMediaPhoto, 
    InputMediaVideo,
    InputFile,
    Update)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import RetryAfter

from config import Config
from handlers.constants.callback_data import CD
from handlers.utils.Exception import TooManyRetries
from handlers.utils.downloader import download_video
from handlers.utils.file_sender import upload_media_to_telegram
from handlers.utils.one_api import InstagramAPI, InstagramFastSaverAPI, InstagramScraperAPI, TikWMFileSaver
from handlers.utils.pydanticmodels import Highlight, MediaItem, OneAPIResponse, InstaUserProfile
from handlers.utils.utils import querify, report_in_channel
from db.models import InstagramAccount

async def get_file_size(url):
    
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            if 'Content-Length' in response.headers:
                file_size = int(response.headers['Content-Length'])
                size =  file_size
            else:
                size =  None  # Content-Length header is missing    
    if size:
        return size / (1024 * 1024) # Convert to MB
    else:
        return None
    
async def get_chunk_sizes(chunk):
    file_sizes = []
    retry_for_getting_a_file_size = 0
    max_retry_for_getting_a_file_size = 2
        
    i = 0
    while i < len(chunk):
            mediaitem = chunk[i]
            try:
                file_size = await get_file_size(url=mediaitem.media)
                retry_for_getting_a_file_size = 0
            except:
                if retry_for_getting_a_file_size < max_retry_for_getting_a_file_size:
                    retry_for_getting_a_file_size += 1
                    continue # retry to get the size of the same file
                file_size = None

            file_sizes.append(file_size) 
            i+=1 # go to next file
    return file_sizes

def there_is_a_file_with_over_20mb_size(sizes:list):
    return any((size > 20 for size in sizes))



def get_clickable_links(
    links:List[str],
    message = """🗂حجم ویدیو بالای ۲۰ مگابایت می باشد. \n\n\n""",
    file_sizes:list|None = None
):
    link_pattern = '<a href="{}"><b>👈 🔗 لینک دانلود مستقیم ویدیو{} {}</b></a>\n\n'
    number_of_links = len(links)

    for number, link in enumerate(links, start=1):
        
        file_size = "" if file_sizes == None else f"[{file_sizes[number-1]:.2f} مگابایت]"
        number = "" if number_of_links == 1 else f"({number}/{number_of_links})"
        message += link_pattern.format(link, number, file_size)
    return message

async def upload_media_and_get_file_id(
        context: ContextTypes.DEFAULT_TYPE, 
        media_type: MediaItem, 
        media_url, 
        retries=3
        )-> None | Tuple[str, str]:
    """
        by default it this function returns none
    """
    for attempt in range(retries):
        try:
            if media_type == "video":
                msg = await context.bot.send_video(
                    chat_id=Config.MEDIA_BANK_CHANNEL,
                    video=media_url,
                )
                if msg.video:
                    return "video", msg.video.file_id
                elif msg.animation:
                    return "animation", msg.animation.file_id
                else:
                    raise Exception("Unexpected response: neither video nor animation returned.")
            elif media_type in ("photo", "image"):
                # msg = await context.bot.send_photo(chat_id=Config.MEDIA_BANK_CHANNEL, photo=media_url)
                return "photo", media_url
            else:
                raise ValueError(f"Unsupported media type: {media_type}")
        except Exception as e:
            logger.info(f"Error in [upload_media_and_get_file_id]: {str(e)}")
            print(e)
    else:
        logger.info(f"Error in [upload_media_and_get_file_id]: Retries ended for this media item. MT: {media_type} : {media_url}")
        # except RetryAfter as e:
        #     wait_time = e.retry_after + 1  # adding a one-second buffer
        #     logger.warning(f"Flood control hit. Retrying in {wait_time} seconds...")
        #     await asyncio.sleep(wait_time)
        #     if retries > 1:
        #         return await upload_media_and_get_file_id(context=context, media_type=media_type, media_url=media_url, retries=retries-1)
        # except Exception as e:        
        #     if attempt < retries - 1:
        #         await asyncio.sleep(1)  # Wait briefly before retrying.
        #     else:
        #         raise e

async def get_instagram_user_id_by_username(username:str):

    user = await InstagramAccount.get_or_none(username = username)

    if user:
        return user.id
    
    InstaAPI = InstagramAPI(token=Config.ONE_API_TOKEN)
    user_info_response = await InstaAPI.user(username=username).fetch()
    user_info = InstaUserProfile(**user_info_response.result)
    await InstagramAccount.create(**user_info.model_dump())
    return user_info.id

async def get_instagram_username_by_id(id:str) -> str | None:

    user = await InstagramAccount.get_or_none(id = id)
    if user:
        return user.username


from telegram import InputMediaPhoto, InputMediaVideo
from typing import List, Union

# Optional: update or import your logger and Config
import logging
logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    # Basic URL check: adjust if needed.
    return url.startswith("http://") or url.startswith("https://")

# async def send_media(
#     update: Update,
#     context: ContextTypes.DEFAULT_TYPE,
#     media_list: List[MediaItem],
#     caption: str = Config.DEFAULT_CAPTION,
#     caption_connected = True,
#     media_group = None,
#     animations = None,
#     files_as_links = None,
#     tries = 0,
# ):
    
#     if len(media_list) > 40:
#         return await context.bot.send_message(
#             chat_id=update.effective_chat.id, 
#             text="درخواست ارسال شما شامل بیش از 40 فایل می باشد. امکان فرستادن این تعداد فایل در اشتراک رایگان وجود ندارد")
#     """
#     Sends media as albums to the chat.
#     returns message or Config.Errors.....
    
#     :param update: The update object.
#     :param context: The context object.
#     :param media_list: A list of media items. Each item can be either a dict 
#                        (with keys 'type' and 'url') or an object with attributes 
#                        'type' and 'url'.
#     :param caption: A caption to attach (only to the first item of the first album).
#     """
    

#     tries +=1
#     if tries > 3:
#         return Config.ERRORS.SENDING_MESSAGE.TOO_MANY_TRIES

#     if animations == None:
#         animations = []
#     if files_as_links == None:
#         files_as_links = []

#     if not isinstance(media_group, list): # IF LIST = REITERATION BECAUSE OF ANIMATION
#         media_group = []
#         for media in media_list:
#             # Determine media type and URL, supporting both dicts and objects.
#             if not media.url or not is_valid_url(media.url):
#                 logger.error(f"Skipping invalid URL: {media.url}")
#                 continue

#             if media.type in ("photo", "image"):
#                 url = media.url # + f"?filename=image.jpeg"
#                 media_group.append(InputMediaPhoto(url))
#             elif media.type == "video":
#                 url = media.url # + f"?filename=vid.mp4"
#                 media_group.append(InputMediaVideo(url))
#             else:
#                 await report_in_channel(context=context, text=f"Unknown media type '{media.type}' for URL: {media.url}")

#         if not media_group:
#             return Config.ERRORS.SENDING_MESSAGE.NO_MEDIA

#     # Helper: split a list into chunks of a given size.
#     def chunk_list(data, chunk_size):
#         for i in range(0, len(data), chunk_size):
#             yield data[i:i + chunk_size]

#     MAX_ITEMS_PER_ALBUM = 10
#     chunks = list(chunk_list(media_group, MAX_ITEMS_PER_ALBUM))

#     # Send each album separately.

#     send_msgs = []
#     chunk_number = 0
#     those_with_wrong_file_identifier = []
#     for chunk in chunks:

#         def filter_media_group(media_group, group):
#             # Create a set of the media attribute for all items in group
#             group_media = {getattr(item, 'media', None) for item in group}
#             # Return only those items whose media attribute is not in the set
#             return [item for item in media_group if getattr(item, 'media', None) not in group_media]

#         media_group = filter_media_group(media_group, chunk)
#         print("media group", media_group)

#         file_sizes = []
#         i = 0
#         retry_for_getting_a_file_size = 0
#         max_retry_for_getting_a_file_size = 2
#         # for mediaitem in chunk:
#         #     try:
#         #         file_size = await get_file_size(url=mediaitem.media)
#         #     except:
#         #         file_size = None
#         #     file_sizes.append(file_size)
#         while i < len(chunk):
#             mediaitem = chunk[i]
#             try:
#                 file_size = await get_file_size(url=mediaitem.media)
#                 retry_for_getting_a_file_size = 0
#             except:
#                 if retry_for_getting_a_file_size < max_retry_for_getting_a_file_size:
#                     retry_for_getting_a_file_size += 1
#                     continue # retry to get the size of the same file
#                 file_size = None

#             file_sizes.append(file_size) 
#             i+=1 # go to next file
        
        

#         if not caption_connected:
#             post_original_caption = caption
#             caption = Config.DEFAULT_CAPTION
        
#         except_needs_recursion = False
        
#         try:
#             if None in file_sizes: # means we couldn't get the file size of at least one file
#             #use NOCORS or send the same links although it might be problematic
#                 context.application.create_task(report_in_channel(context=context, text=str(chunk)+ "\n\n" + str(file_sizes)))
#                 return Config.ERRORS.SENDING_MESSAGE.PROBLEMATIC_LINK_OR_INABILITY_TO_CHECK_SIZE
#             elif there_is_a_file_with_over_20mb_size(file_sizes):
#                 print("file with over 20 mg size")
#                 send_msgs = await context.bot.send_message(
#                             chat_id=update.effective_chat.id, 
#                             text=get_clickable_links(
#                                 links=[mediaitem.media for mediaitem in chunk],
#                                 file_sizes=file_sizes),
#                             parse_mode=ParseMode.HTML
#                             )
#             else:
#                 send_msgs = await context.bot.send_media_group(
#                     chat_id = update.effective_chat.id,
#                     media = chunk,
                    
#                 )
#                 send_msgs = await context.bot.send_message(
#                     chat_id=update.effective_chat.id,
#                     text= caption
#                     )
#                 if not caption_connected:
#                     await context.bot.send_message(
#                         chat_id=update.effective_chat.id,
#                         text= post_original_caption)
                    
#         except (Forbidden, TimeoutError) as e:
#             media_group.extend(chunk)

#             error_message= str(e)
#             error_type = "Forbidden" if isinstance(e, Forbidden) else "Timed out error"
            
#             err_report = "{error_type}:" + error_message
#             logger.critical(msg=err_report)
#             context.application.create_task(report_in_channel(context=context, text=err_report))

#             if isinstance(e, TimeoutError):
#                 except_needs_recursion = True
#             else:
#                 return Config.ERRORS.SENDING_MESSAGE.FORBIDDEN
#         except BadRequest as e:
            
#             error_message= str(e)
#             logger.info(msg="Bad_request: " + error_message)
#             context.application.create_task(report_in_channel(context=context, text="Bad_request: " + error_message))
            
#             if "webpage_media_empty" in error_message:
#                 for mediaitem in chunk:
#                     try:
#                         send_msgs = await context.bot.send_document(
#                             chat_id=update.effective_chat.id, 
#                             document=mediaitem.media
#                             )
#                     except:
#                         send_msgs = await context.bot.send_message(
#                             chat_id=update.effective_chat.id, 
#                             text=get_clickable_links(
#                                 [mediaitem.media], 
#                                 message="مشکلی در ارسال فایل پیش آمد \n"),
#                             parse_mode=ParseMode.HTML
#                             )
                    
#                     await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
#                 continue  
#             elif "caption" in error_message:
#                 media_group.extend(chunk)

#                 caption_connected = False
#                 except_needs_recursion = True
            
#             elif "wrong file identifier" in error_message:
#                 # it is an animation
#                 logger.critical("Wrong file identifier")
#                 # those_with_wrong_file_identifier += [mediaitem.media for mediaitem in chunk]
#                 for mediaitem in chunk:
#                     try:
#                         send_msgs = await context.bot.send_document(chat_id=update.effective_chat.id, document=mediaitem.media)
#                     except Exception as e:
#                         send_msgs = await context.bot.send_message(
#                             chat_id=update.effective_chat.id, 
#                             text=get_clickable_links([mediaitem.media]),
#                             parse_mode=ParseMode.HTML
#                             )
#                     await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)

#                 continue
#                 # logger.error(f"Failed to send album {chunk_number+1}/{len(chunks)+1}: {e}")
#                 # print(chunks)

#                 # rest_every_5_files = 2
#                 # x_files_sent = 0
#                 # for mediaitem in chunk:
#                 #     x_files_sent+=1
#                 #     if x_files_sent %5 == 0:
#                 #         await asyncio.sleep(rest_every_5_files)
#                 #     media_type = "video" if isinstance(mediaitem, InputMediaVideo) else 'photo'
                    
#                 #     file_result = await upload_media_and_get_file_id(
#                 #         context=context, 
#                 #         media_type=media_type, 
#                 #         media_url=mediaitem.media
#                 #         )
#                 #     if file_result == None:
#                 #         continue

#                 #     print(file_result)

#                 #     file_type, file_id = file_result

                    
#                 #     if file_type=="video":
#                 #         media_group.append(mediaitem)
#                 #     elif file_type=="photo":
#                 #         media_group.append(mediaitem)
#                 #     else: 
#                 #         # remove the problematic animation from the list
#                 #         animations += [file_id]
                
#                 media_group = None if not media_group else media_group
#                 animations = None if not animations else animations
#                 message = ""
#             elif "webpage_curl_failed" in error_message:
#                 for mediaitem in chunk:
#                     send_msgs = await context.bot.send_document(chat_id=update.effective_chat.id, document=mediaitem.media)
#                     await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                
#                 continue
        
#         if except_needs_recursion:
#             send_msgs = await send_media(
#                         update=update, 
#                         context=context, 
#                         media_list=media_list, 
#                         caption= caption,
#                         caption_connected=caption_connected, 
#                         media_group=media_group, 
#                         animations=animations,
#                         # files_as_links=files_as_links,
#                         tries= tries)
#             return send_msgs
                

#     # x= 1
#     # if animations:
#     #     for animation in animations:
#     #         send_msgs = await context.bot.send_animation(chat_id=update.effective_chat.id, animation=animation)
#     #         if x%5 == 0:
#     #             await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)

#     # if files_as_links:
#     #     # links = get_clickable_links(files_as_links)
#     #     # send_msgs = await context.bot.send_message(
#     #     #     chat_id=update.effective_chat.id, 
#     #     #     text= links, 
#     #     #     parse_mode=ParseMode.HTML)
#     #     for file in files_as_links:
#     #         send_msgs = await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
#     #         await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
        
#     return send_msgs


async def send_user_highlights(chat_id, context: ContextTypes.DEFAULT_TYPE, highlights:List[Highlight]):

    if not highlights:
        return await context.bot.send_message(
            chat_id=chat_id, 
            text="🔍 هایلایتی برای این کاربر یافت نشد. (تعداد هایلایت: 0)", 
        )

    keyboard = []
    keyboard_line = []
    for highlight in highlights:
        if len(keyboard_line)==2:
            keyboard.append(keyboard_line)
            keyboard_line = []
        else:
            keyboard_line.append(InlineKeyboardButton(text=highlight.title, callback_data=querify(CD.DL_HIGHLIGHT, highlight.id)))

    return await context.bot.send_message(
        chat_id=chat_id, 
        text="🗃 لیست هایلایت های کاربر:", 
        reply_markup=InlineKeyboardMarkup(keyboard))

def complies_with_cache_policies(saved_at: datetime.datetime, request_type: str) -> bool:
    """Checks if a request complies with cache policies based on saved time and request type."""
    cache_seconds = Config.CACHE_TIME[request_type]  # Get cache duration in seconds
    cache_time = datetime.timedelta(seconds=cache_seconds)

    # Ensure `saved_at` is UTC-aware
    if saved_at.tzinfo is None:
        saved_at = saved_at.replace(tzinfo=datetime.timezone.utc)

    # Correct the time difference calculation
    expiration_time = saved_at + cache_time
    remaining_time = expiration_time - datetime.datetime.now(datetime.timezone.utc)

    # print(f"Saved At: {saved_at}, Expiration Time: {expiration_time}, Remaining Time: {remaining_time.total_seconds()}")

    # Return True if the cache is still valid (remaining time is positive)
    return remaining_time.total_seconds() > 0


async def get_one_api_req_object(type_of_request, params, link, share_in_url):
    """
        returns None if the request is not handlable by oneapi
    """

    insta_API = InstagramAPI(Config.ONE_API_TOKEN)
    
    match type_of_request:
        case Config.INSTAGRAM_REUQEST_TYPES.POST:
            if share_in_url:
                # api_provider = Config.SERVICE_PROVIDERS.FASTSAVERAPI
                # api_req = InstagramFastSaverAPI(Config.FASTSAVERAPI_TOKEN).get(url=link)
                return None
            else:    
                api_req= insta_API.post(shortcode=params[0])
        case Config.INSTAGRAM_REUQEST_TYPES.REEL:
            if share_in_url:
                # api_provider = Config.SERVICE_PROVIDERS.FASTSAVERAPI
                # api_req = InstagramFastSaverAPI(Config.FASTSAVERAPI_TOKEN).get(url=link)
                return None
            else:    
                api_req= insta_API.reel(shortcode=params[0])
            
        case Config.INSTAGRAM_REUQEST_TYPES.USER_INFO:

            api_req = insta_API.user(username=params[0])
        case Config.INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS:
            user_name_or_id = params[0]
            if user_name_or_id.isdigit():
                user_id = user_name_or_id
            else:
                user_id = await get_instagram_user_id_by_username(username=params[0]) 
            api_req= insta_API.highlights(user_id=user_id)

        case Config.INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES:
            if params[0].isdigit():
                api_req= insta_API.highlight(highlight_id=params[0])
            else:
                # api_provider = Config.SERVICE_PROVIDERS.FASTSAVERAPI
                # api_req = InstagramFastSaverAPI(Config.FASTSAVERAPI_TOKEN).get(url=link)
                return None
        case Config.INSTAGRAM_REUQEST_TYPES.STORIES | Config.INSTAGRAM_REUQEST_TYPES.STORY:

            user_name_or_id = params[0]
            if user_name_or_id.isdigit():
                user_id = user_name_or_id
            else:
                user_id = await get_instagram_user_id_by_username(username=params[0]) 
            api_req= insta_API.stories(user_id=user_id)
    return api_req

async def get_fastsaverapi_req_object(link):
    return InstagramFastSaverAPI(Config.FASTSAVERAPI_TOKEN).get(url=link)

async def get_tikvm_req_object(link):
    return TikWMFileSaver(Config.FASTSAVERAPI_TOKEN).get(url=link)


async def get_insta_scraper_api_req_object(type_of_request, params, link):
    
    insta_scraper_api = InstagramScraperAPI(token=Config.INSTA_SCRAPER_TOKEN)
    
    match type_of_request:
        case Config.INSTAGRAM_REUQEST_TYPES.USER_INFO:
            api_req = insta_scraper_api.get_user_profile_info(username_or_id_or_url=params[0])
        case Config.INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS:
            api_req = insta_scraper_api.highlights(username_or_id_or_url=params[0])
        case (
            Config.INSTAGRAM_REUQEST_TYPES.STORY | 
            Config.INSTAGRAM_REUQEST_TYPES.POST | 
            Config.INSTAGRAM_REUQEST_TYPES.REEL | 
            Config.INSTAGRAM_REUQEST_TYPES.TV |
            Config.INSTAGRAM_REUQEST_TYPES.JUST_SHARE):
            api_req = insta_scraper_api.get_info(code_or_id_or_url=link)
    
    return api_req


def caption_size_meets_telegram_standards(caption:str)-> bool:
    TELEGRAM_CAPTION_LIMIT = 1024
    return len(caption) <= TELEGRAM_CAPTION_LIMIT - 24


async def download_and_send_file_to_user(
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    link
    ):

    file_path = await download_video(
        video_url= link,
        save_folder=Config.FILE_SAVE_FOLDER,
    )

    if not file_path:

        return
    
    try:
        sent_file = await upload_media_to_telegram(
            context=context,
            update=update,
            media_path=file_path
            )
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File deleted successfully.")
        else:
            print("File does not exist.")
    
