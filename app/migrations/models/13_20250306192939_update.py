from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_at" TYPE TIMESTAMPTZ USING "joined_at"::TIMESTAMPTZ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_at" TYPE TIMESTAMPTZ USING "joined_at"::TIMESTAMPTZ;"""
