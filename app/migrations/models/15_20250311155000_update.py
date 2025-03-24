from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "channel" ADD "acceptor_message_id" INT;
        ALTER TABLE "channel" ADD CONSTRAINT "fk_channel_message_6d6a854f" FOREIGN KEY ("acceptor_message_id") REFERENCES "message" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "channel" DROP CONSTRAINT "fk_channel_message_6d6a854f";
        ALTER TABLE "channel" DROP COLUMN "acceptor_message_id";"""
