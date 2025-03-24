from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "broadcastrequest" ADD "is_finished" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "broadcastrequest" ADD "is_underway" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_successfully_sent_messages" SET DEFAULT 0;
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_users_already_covered" SET DEFAULT 0;
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_users_to_be_sent_to" SET DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "broadcastrequest" DROP COLUMN "is_finished";
        ALTER TABLE "broadcastrequest" DROP COLUMN "is_underway";
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_successfully_sent_messages" DROP DEFAULT;
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_users_already_covered" DROP DEFAULT;
        ALTER TABLE "broadcastrequest" ALTER COLUMN "n_of_users_to_be_sent_to" DROP DEFAULT;"""
