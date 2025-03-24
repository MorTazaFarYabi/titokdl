from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ALTER COLUMN "media_id" TYPE TEXT USING "media_id"::TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ALTER COLUMN "media_id" TYPE VARCHAR(150) USING "media_id"::VARCHAR(150);"""
