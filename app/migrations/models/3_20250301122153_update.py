from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ALTER COLUMN "origin_chat_id" SET DEFAULT 0;
        ALTER TABLE "message" ALTER COLUMN "telegram_message_id" SET DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ALTER COLUMN "origin_chat_id" DROP DEFAULT;
        ALTER TABLE "message" ALTER COLUMN "telegram_message_id" DROP DEFAULT;"""
