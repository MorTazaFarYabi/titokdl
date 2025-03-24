import logging

from handlers.utils.downloader import download_video
logger = logging.getLogger(__name__)

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
    Update, Message)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import RetryAfter

from config import Config
from handlers.constants.callback_data import CD
from handlers.utils.Exception import TooManyRetries
from handlers.utils.downloader_utils import caption_size_meets_telegram_standards, download_and_send_file_to_user, get_chunk_sizes, get_clickable_links, get_file_size, is_valid_url, there_is_a_file_with_over_20mb_size
from handlers.utils.one_api import InstagramAPI, InstagramFastSaverAPI, InstagramScraperAPI
from handlers.utils.pydanticmodels import Highlight, MediaItem, OneAPIResponse, InstaUserProfile
from handlers.utils.utils import querify, report_in_channel
from db.models import InstagramAccount




async def download_file(file_url, save_folder=Config.FILE_SAVE_FOLDER):
    """
    Asynchronously downloads an Instagram video and saves it with its original filename.

    :param file_url: str - The URL of the Instagram video.
    :param save_folder: str - Folder to save the downloaded video.
    """
    headers = {"User-Agent": "Mozilla/5.0"}  # Prevents bot detection

    # Extract filename from URL
    parsed_url = urlparse(file_url)
    filename = os.path.basename(parsed_url.path)  # Extracts original filename
    if not filename:  # Fallback if no filename is detected
        filename = "instagram_video.mp4"

    # # Ensure save directory exists
    # os.makedirs(save_folder, exist_ok=True)

    # Define full save path
    save_path = os.path.join(save_folder, filename)

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    with open(save_path, "wb") as file:
                        while True:
                            chunk = await response.content.read(8192)  # Asynchronous chunk reading


                            if not chunk:
                                break
                            file.write(chunk)
                else:
                    print(f"❌ Failed to download video. HTTP Status: {response.status}")
    except Exception as e:
        print(f"❌ Download failed: {e}")

    return save_path



async def upload_media_to_telegram(
    context: ContextTypes.DEFAULT_TYPE,
    update:Update, 
    media_path
):
    """
    Sends any type of Instagram media (photo/video) to the Telegram user.

    :param bot_token: str - Your Telegram bot's API token.
    :param chat_id: int - The Telegram chat ID of the user.
    :param media_path: str - The path to the downloaded media file.
    """

    if not os.path.exists(media_path):  # Check if file exists before sending
        print("❌ Error: Media file not found!")
        return

    # Detect file type using mimetypes
    media_type, _ = guess_type(media_path)

    try:
        with open(media_path, "rb") as media_file:
            if media_type and media_type.startswith("image"):
                media_type="photo"
                msg = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=media_file, 
                    caption="🖼️ Here is your Instagram image!"
                    )

            elif media_type and media_type.startswith("video"):
                media_type="video"
                msg = await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=media_file, 
                    caption="🖼️ Here is your Instagram image!"
                    )
            elif media_type and media_type.startswith("audio"):
                media_type="audio"
                msg = await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=media_file, 
                    caption="🖼️ Here is your Instagram image!"
                    )

            else:
                return print(f"⚠️ Unsupported media type: {media_type}")
    except Exception as e:
        return print(f"❌ Failed to send media: {e}")

    return msg
    # return media_type, file_id
    



async def download_and_send_file_to_user(
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    link
    ):

    file_path = await download_file(
        file_url= link,
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
    


async def send_as_document_or_link( 
    context: ContextTypes.DEFAULT_TYPE,
    chat_id:str,
    link:str,
    file_sizes: list|None = None
    ) -> Message:

    

    # print(f"file sizes: {file_sizes}")
    try:
        send_msgs = await context.bot.send_document(
        chat_id=chat_id,
        document=link
        )
    except:
        send_msgs = await context.bot.send_message(
        chat_id=chat_id, 
        text=get_clickable_links(
            [link],
            file_sizes= file_sizes,
            message= """🗂 برای دانلود فایل لطفا از لینک زیر استفاده کنید.  \n\n"""
            ),
        parse_mode=ParseMode.HTML
        )
    return send_msgs


async def send_chunk(    
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chunk:list,
    # media_list: List[MediaItem],
    # caption: str = Config.DEFAULT_CAPTION,
    caption_connected = True,
    post_original_caption = "",
    # media_group = None,
    # animations = None,
    # files_as_links = None,
    tries = 0,
    file_sizes = None,
    request_url = ""
    ):
        
        tries +=1
        if tries > 3:
            return Config.ERRORS.SENDING_MESSAGE.TOO_MANY_TRIES
        if not file_sizes:
            file_sizes = await get_chunk_sizes(chunk)        
        caption = f"{post_original_caption} \n\n {Config.DEFAULT_CAPTION}"
        caption = caption.replace('\\n', '\n')
        
        try:
            if None in file_sizes: # means we couldn't get the file size of at least one file
            #use NOCORS or send the same links although it might be problematic
                
                errmsg = f"URL: {request_url}\n\nthere was None in filesizes:\n\n {str(file_sizes)} \n\n"
                for n, mediaitem in enumerate(chunk, start=1):
                    errmsg+= f'<a href="{mediaitem.media}">{n}</a>\n\n'
                context.application.create_task(report_in_channel(
                    context=context, 
                    text=errmsg,
                ))

                # send_msgs = await context.bot.send_message(
                #             chat_id=update.effective_chat.id, 
                #             text=get_clickable_links([mediaitem.media for mediaitem in chunk]),
                #             parse_mode=ParseMode.HTML
                #             )

                return Config.ERRORS.SENDING_MESSAGE.PROBLEMATIC_LINK_OR_INABILITY_TO_CHECK_SIZE
            elif there_is_a_file_with_over_20mb_size(file_sizes):

                
                # send_msgs = await context.bot.send_message(
                #             chat_id=update.effective_chat.id, 
                #             text=get_clickable_links(
                #                 links=[mediaitem.media for mediaitem in chunk],
                #                 file_sizes=file_sizes,
                #                 message= """🗂حجم ویدیو بالای ۲۰ مگابایت می باشد. \n\n\n"""
                #                 ),
                            
                #             parse_mode=ParseMode.HTML
                #             )

                send_msgs = await download_and_send_file_to_user(
                    context=context,
                    update= update,
                    link= mediaitem.media
                )
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                
                if file_sizes < 50:
                    context.application.create_task(download_and_send_file_to_user(
                        context=context,
                        update=update,
                        link=chunk[0].media
                    ))
            else:
                # print(file_sizes)
                if caption_connected and caption_size_meets_telegram_standards(caption):
                    send_msgs = await context.bot.send_media_group(
                        chat_id = update.effective_chat.id,
                        media = chunk,
                        caption = caption
                    )
                else:
                    send_msgs = await context.bot.send_media_group(
                        chat_id = update.effective_chat.id,
                        media = chunk,
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                    
        except (Forbidden, TimeoutError) as e:
            # media_group.extend(chunk)
            error_message= str(e)
            error_type = "Forbidden" if isinstance(e, Forbidden) else "Timed out error"
            
            err_report = f"link: {request_url} \n\n {error_type}:" + error_message
            context.application.create_task(report_in_channel(context=context, text=err_report))

            if isinstance(e, TimeoutError):
                except_needs_recursion = True
                return await send_chunk(
                    update=update,
                    context=context,
                    chunk=chunk,
                    caption_connected=caption_connected,
                    post_original_caption=post_original_caption,
                    tries = tries,
                    file_sizes=file_sizes,
                    request_url = request_url
                )
            else:
                return Config.ERRORS.SENDING_MESSAGE.FORBIDDEN
        except BadRequest as e:
            
            error_message= str(e)
            dl_links = "\n\n".join([f'<a href="{mediaitem.media}">{n}</a>' for n, mediaitem in enumerate(chunk, start=1)])

            context.application.create_task(report_in_channel(
                context=context, 
                text=f"URL: {request_url}\n\n Bad_request: {error_message} \n\n {file_sizes} \n\n {dl_links}"
                ))
            
            if "webpage_media_empty" in error_message:
                for mediaitem in chunk:
                    send_msgs = await send_as_document_or_link(
                        context=context,
                        chat_id = update.effective_chat.id,
                        link = mediaitem.media,
                        # file_sizes=file_sizes
                    )    
                    await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                      
            elif "caption" in error_message:
                # media_group.extend(chunk)

                caption_connected = False
                return await send_chunk(
                    update=update,
                    context=context,
                    chunk=chunk,
                    caption_connected=caption_connected,
                    post_original_caption=post_original_caption,
                    tries = tries,
                    file_sizes=file_sizes,
                    request_url = request_url
                )
            
            elif "wrong file identifier" in error_message:
                # it is an animation
                # those_with_wrong_file_identifier += [mediaitem.media for mediaitem in chunk]
                for mediaitem in chunk:
                    send_msgs = await send_as_document_or_link(
                        context=context,
                        chat_id = update.effective_chat.id,
                        link = mediaitem.media,
                        # file_sizes=file_sizes
                    )    
                    await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                
            elif "webpage_curl_failed" in error_message:
                for mediaitem in chunk:
                    send_msgs = await send_as_document_or_link(
                        context=context,
                        chat_id = update.effective_chat.id,
                        link = mediaitem.media,
                        # file_sizes=file_sizes
                    )    
                    await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                
                
            elif "Wrong type of the web page content" in error_message:
                for mediaitem in chunk:
                    send_msgs = await send_as_document_or_link(
                        context=context,
                        chat_id = update.effective_chat.id,
                        link = mediaitem.media,
                        # file_sizes=file_sizes
                    )    
                    await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )
                
            elif "Failed to get http url content" in error_message:
                for mediaitem in chunk:
                    send_msgs = await send_as_document_or_link(
                        context=context,
                        chat_id = update.effective_chat.id,
                        link = mediaitem.media,
                        # file_sizes=file_sizes
                    )    
                    await asyncio.sleep(Config.TELEGRAM_LIMIT_FOR_SENDING_MESSAGES.PRIVATE)
                await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text= caption
                        )

            else:
                return Config.ERRORS.SENDING_MESSAGE.UNKNOWN_ERROR
            
        return send_msgs


async def send_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_list: List[MediaItem],
    caption: str = "",
    caption_connected = True,
    media_group = None,
    animations = None,
    files_as_links = None,
    tries = 0,
    request_url = ""
):
    
    if len(media_list) > 40:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="درخواست ارسال شما شامل بیش از 40 فایل می باشد. امکان فرستادن این تعداد فایل در اشتراک رایگان وجود ندارد")
    """
    Sends media as albums to the chat.
    returns message or Config.Errors.....
    
    :param update: The update object.
    :param context: The context object.
    :param media_list: A list of media items. Each item can be either a dict 
                       (with keys 'type' and 'url') or an object with attributes 
                       'type' and 'url'.
    :param caption: A caption to attach (only to the first item of the first album).
    """
    

    tries +=1
    if tries > 3:
        return Config.ERRORS.SENDING_MESSAGE.TOO_MANY_TRIES

    if animations == None:
        animations = []
    if files_as_links == None:
        files_as_links = []

    if not isinstance(media_group, list): # IF LIST = REITERATION BECAUSE OF ANIMATION
        media_group = []
        for media in media_list:
            # Determine media type and URL, supporting both dicts and objects.
            if not media.url or not is_valid_url(media.url):
                context.application.create_task(
                    report_in_channel(context=context, text=f"Skipping invalid URL: {media.url}")
                )
                # logger.error(f"Skipping invalid URL: {media.url}")
                continue

            if media.type in ("photo", "image"):
                url = media.url # + f"?filename=image.jpeg"
                media_group.append(InputMediaPhoto(url))
            elif media.type == "video":
                url = media.url # + f"?filename=vid.mp4"
                media_group.append(InputMediaVideo(url))
            else:
                context.application.create_task(
                    report_in_channel(context=context, text=f"Unknown media type '{media.type}' for URL: {media.url}")
                )

        if not media_group:
            return Config.ERRORS.SENDING_MESSAGE.NO_MEDIA

    # Helper: split a list into chunks of a given size.
    def chunk_list(data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    MAX_ITEMS_PER_ALBUM = 10
    chunks = list(chunk_list(media_group, MAX_ITEMS_PER_ALBUM))

    # Send each album separately.

    send_msgs = []
    chunk_number = 0
    those_with_wrong_file_identifier = []
    for chunk in chunks:
        send_msgs = await send_chunk(
            update=update,
            context=context,
            chunk=chunk,
            caption_connected=caption_connected,
            post_original_caption= caption,
            request_url = request_url
            )
        ### >>> here we should deal with the possible errors that sending each chunk might return and inform the user
        
    return send_msgs

                