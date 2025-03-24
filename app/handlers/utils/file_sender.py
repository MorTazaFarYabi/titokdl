import os
from mimetypes import guess_type

from telegram import Update
from telegram.ext import ContextTypes


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

            else:
                return print(f"⚠️ Unsupported media type: {media_type}")
    except Exception as e:
        return print(f"❌ Failed to send media: {e}")

    return msg
    return media_type, file_id
    