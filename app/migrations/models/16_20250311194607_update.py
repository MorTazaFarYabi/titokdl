from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ADD "keyboard" JSONB NOT NULL;
        ALTER TABLE "message" ADD "reply_markup_type" VARCHAR(1) NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" DROP COLUMN "keyboard";
        ALTER TABLE "message" DROP COLUMN "reply_markup_type";"""
