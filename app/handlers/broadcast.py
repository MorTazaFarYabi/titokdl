import asyncio
import sqlite3
from telegram.ext import ContextTypes
from telegram.error import (TelegramError, RetryAfter, TimedOut,
                            NetworkError, BadRequest, Forbidden)
from db.models import BroadCastRequest, User, Message
from handlers.utils.utils import report_in_channel, send_a_db_message


import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def get_user_chunks(chunk_size: int, offset=0, limit=0):
    users_delivered = 0
    while True:
        # Fetch a chunk of users
        users = await User.filter(
            has_started=True, 
            has_blocked_the_bot = False,
            ).offset(offset).limit(chunk_size).all()
        if not users:
            break
        
        # Update users delivered by the actual number of users in this chunk
        users_delivered += len(users)
        
        # Check if we've reached the limit
        if limit and users_delivered > limit:
            # Optionally, slice the list to only include the remaining users
            excess = users_delivered - limit
            if excess > 0:
                users = users[:-excess]
            yield users
            break

        yield users
        offset += chunk_size


async def broadcast_message(
        context:ContextTypes.DEFAULT_TYPE, 
        broadcast_id: BroadCastRequest,
        chunk_size: int = 100
        ):
    """
    Sends the given message to a specified number of users in the database while respecting the Telegram rate limit.
    
    Args:
        context: includes an Instance of telegram.Bot to send messages.
        broadcast_id: to fetch the broadcast
        chunk_size: How many users to fetch from the DB at a time.
    """

    # Delay between messages to avoid rate limits.
    broadcast_request = await BroadCastRequest.filter(id = broadcast_id).prefetch_related('message').first()
    message = broadcast_request.message
    delay = 1 / broadcast_request.messages_per_second
    
    # used to avoid sending messages to users who have already received it before the broadcast was paused and resumed again
    initial_offset = broadcast_request.n_of_users_already_covered
    number_of_users_to_receive_it = broadcast_request.n_of_users_to_be_sent_to

    async for chunk in get_user_chunks(chunk_size, initial_offset, number_of_users_to_receive_it):

        if not broadcast_request.is_underway:
            # broadcast was paused in the middle of the process by the admin
            # it the admin started the broadcast again broadcast_message... 
            # ...would be called and initial_offset avoids repeated msgs to the same user 
            break
        
        successfully_sent_to_x_users_in_chunk = 0

        for user in chunk:
            chat_id = user.id

            if user.has_blocked_the_bot or user.is_bot:
                continue

            try:
                await send_a_db_message(context=context, db_msg=message, chat_id=chat_id)
                successfully_sent_to_x_users_in_chunk+=1
            except RetryAfter as e:
                # Telegram rate limit hit; wait for the specified retry time.
                logger.info(f"Rate limit hit for {chat_id}. Waiting for {e.retry_after} seconds.")
                await asyncio.sleep(e.retry_after)
                try:
                    await send_a_db_message(context=context, db_msg=message, chat_id=chat_id)
                    successfully_sent_to_x_users_in_chunk+=1
                except Exception as inner_e:
                    logger.info(f"Failed to resend message to {chat_id} after rate limit: {inner_e}")
            except (TimedOut, NetworkError) as e:
                # Network issues; wait a short while and try once more.
                logger.info(f"Network issue for {chat_id}: {e}. Retrying after 5 seconds.")
                await asyncio.sleep(5)
                try:
                    await send_a_db_message(context=context, db_msg=message, chat_id=chat_id)
                    successfully_sent_to_x_users_in_chunk+=1
                except Exception as inner_e:
                    logger.info(f"Failed to send message to {chat_id} after network error: {inner_e}")
            except Forbidden as e:
                # The bot was blocked or the chat is invalid. Log and continue.
                logger.info(f"Unauthorized to send message to {chat_id}: {e}")
                try:
                    user.has_blocked_the_bot = True
                    await user.save()
                except Exception as e:
                    logger.info(f"updating user error: {e}")
                    pass
            except BadRequest as e:
                # Likely an invalid chat_id or malformed message. Log and continue.
                logger.info(f"Bad request for {chat_id}: {e}")
            except TelegramError as e:
                # Catch-all for other Telegram-related errors.
                logger.info(f"Telegram error for {chat_id}: {e}")
            # Wait a bit before sending the next message to respect the rate limit.
            except Exception as e:
                await report_in_channel(
                    context=context,
                    text= f"❌❌❌❌ unhandled error in broadcasting: {str(e)}",
                )
            await asyncio.sleep(delay)
                                
        broadcast_request.n_of_users_already_covered += len(chunk)
        broadcast_request.n_of_successfully_sent_messages += successfully_sent_to_x_users_in_chunk

        if broadcast_request.n_of_users_already_covered >= broadcast_request.n_of_users_to_be_sent_to:
            broadcast_request.is_finished = True
            broadcast_request.is_underway = False

        await broadcast_request.save()

            

# Example usage:
# if __name__ == '__main__':
#     # Configuration parameters
#     DB_PATH = "users.db"  # Your SQLite database file with a 'users' table.
#     BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
#     CHAT_MESSAGE = "Hello! This is a broadcast message."
#     RATE_PER_MINUTE = 20  # Number of messages per minute.
    
#     bot = Bot(token=BOT_TOKEN)
    
#     # Run the broadcast as an asynchronous task.
#     asyncio.run(broadcast_message(bot, CHAT_MESSAGE, RATE_PER_MINUTE, DB_PATH))
