from telegram.ext import Application
from telegram import Update
from config import Config

def get(token, polling = False):

    if polling:
        return (
            Application.builder()
            .base_url(base_url="http://65.109.220.132:8081/bot")
            .base_file_url(base_file_url="http://65.109.220.132:8081/bot")
            .token(token) # replace <your-bot-token>
            .read_timeout(Config.HTTPX_READ_TIMEOUT_SECONDS)
            .connection_pool_size(Config.HTTPX_CONNECTION_POOL_SIZE)
            .concurrent_updates(Config.BOT_CONCURRENT_UPDATE_MANAGEMENT)
            .get_updates_read_timeout(42)
            .build()
        )
    
    return (
        Application.builder()
        .base_url(base_url="http://65.109.220.132:8081/bot")
        .base_file_url(base_file_url="http://65.109.220.132:8081/bot")
        .updater(None)
        .token(token) # replace <your-bot-token>
        .read_timeout(Config.HTTPX_READ_TIMEOUT_SECONDS)
        .connection_pool_size(Config.HTTPX_CONNECTION_POOL_SIZE)
        .concurrent_updates(Config.BOT_CONCURRENT_UPDATE_MANAGEMENT)
        .get_updates_read_timeout(42)
        .build()
    )

async def process_update(ptb, request):
    req = request
    update = Update.de_json(req, ptb.bot)
    # async with ptb:
    #     await ptb.start()
    await ptb.process_update(update)
        # await ptb.stop()