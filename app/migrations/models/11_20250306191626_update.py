from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_from" SET DEFAULT 'I';
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_at" DROP NOT NULL;
        ALTER TABLE "user" ADD "is_from_joining_a_chat" BOOL NOT NULL  DEFAULT False;
        CREATE TABLE IF NOT EXISTS "userbalance" (
    "id" SERIAL NOT NULL PRIMARY KEY
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "is_from_joining_a_chat";
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_from" DROP DEFAULT;
        ALTER TABLE "channelmembership" ALTER COLUMN "joined_at" SET NOT NULL;
        DROP TABLE IF EXISTS "userbalance";"""
