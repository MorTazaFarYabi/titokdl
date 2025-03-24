import asyncio
from contextlib import asynccontextmanager
from http import HTTPStatus
import json
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from telegram import Update

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
application = botInstance.get(token)



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

@asynccontextmanager
async def lifespan(_: FastAPI):
    await application.bot.setWebhook(
        Config.WEBHOOK_URL, 
        allowed_updates= allowed_updates
        )
    print(Config.WEBHOOK_URL)
    
    async with application:
        await start_db()
        # global db_cache 
        # db_cache = DBCache()

        await application.start()
        await bot_installer.set_defaults()
        set_handlers(application)
        
        yield

        await application.stop()
        await close_db()


app = FastAPI(lifespan=lifespan)


@app.post("/")
async def get_telegram_request(request: Request):
    # ✅ Read request data BEFORE creating the background task
    request_data = await request.json()
    print(await application.bot.log_out())
    
    # ✅ Process the update in the background
    create_task(botInstance.process_update(application, request_data))  
    
    # ✅ Send an immediate 200 OK response
    return Response(status_code=HTTPStatus.OK)


@app.get("/")
async def get_telegram_request(request: Request):
    return Response(content="hi", status_code=HTTPStatus.OK)
