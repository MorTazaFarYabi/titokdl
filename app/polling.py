import asyncio
from time import sleep

from config import Config

import botInstance
# ngrok http 8000

from db.config import close_db, start_db
from db.models import User
import bot_installer

from handlers.dbcache_manager import DBCache
from handlers.handler_mapping import set_handlers
from pathlib import Path
from asyncio import create_task


token = Config.BOT_TOKEN


# Create (or get) the singleton instance
db_cache = ""


allowed_updates = [
            'message', 
            'edited_message', 
            'channel_post', 
            'inline_query', 
            'chosen_inline_result', 
            'callback_query', 
            'poll',
            'poll_answer',
            'my_chat_member',
            'chat_member',
            'chat_join_request'
            ]




async def main() -> None:
    """Start the bot and manage DB connections."""
    
    # Start your DB before entering the bot context
    
    await start_db()
    await bot_installer.set_defaults()

    # Create the application instance and set handlers
    application = botInstance.get(token, polling=True)
    # print(await application.bot.log_out())
    set_handlers(application) 

    async with application:  # This calls initialize() on entry and shutdown() on exit.
        try:
            await application.start()
            await application.updater.start_polling(poll_interval=1, allowed_updates=allowed_updates)
            # Instead of an infinite loop with sleep, use idle() if available.
            while True:
                
                await asyncio.sleep(.5)
        except Exception as e:
            # Log the exception for debugging
            print(f"Error during polling: {e}")
        finally:
            await application.updater.stop()
            await application.stop()

    # Only close the DB after the bot has fully shut down.
    await close_db() 


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        
        pass