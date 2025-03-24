import aiohttp
import asyncio
import os
from urllib.parse import urlparse
from config import Config

async def download_video(video_url, save_folder=Config.FILE_SAVE_FOLDER):
    """
    Asynchronously downloads an Instagram video and saves it with its original filename.

    :param video_url: str - The URL of the Instagram video.
    :param save_folder: str - Folder to save the downloaded video.
    """
    headers = {"User-Agent": "Mozilla/5.0"}  # Prevents bot detection

    # Extract filename from URL
    parsed_url = urlparse(video_url)
    filename = os.path.basename(parsed_url.path)  # Extracts original filename
    if not filename:  # Fallback if no filename is detected
        filename = "instagram_video.mp4"

    # # Ensure save directory exists
    # os.makedirs(save_folder, exist_ok=True)

    # Define full save path
    save_path = os.path.join(save_folder, filename)

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(video_url) as response:
                if response.status == 200:
                    with open(save_path, "wb") as file:
                        while True:
                            chunk = await response.content.read(8192)  # Asynchronous chunk reading
                            if not chunk:
                                break
                            file.write(chunk)
                    # print(f"\n✅ Video downloaded successfully: {save_path}")
                else:
                    print(f"❌ Failed to download video. HTTP Status: {response.status}")
    except Exception as e:
        print(f"❌ Download failed: {e}")

    return save_path

