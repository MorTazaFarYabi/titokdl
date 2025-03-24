from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "broadcastrequest" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "messages_per_second" INT NOT NULL,
    "n_of_successfully_sent_messages" INT NOT NULL,
    "n_of_users_already_covered" INT NOT NULL,
    "n_of_users_to_be_sent_to" INT NOT NULL,
    "message_id" INT NOT NULL REFERENCES "message" ("id") ON DELETE CASCADE
);
        ALTER TABLE "message" ADD "telegram_message_id" INT NOT NULL;
        ALTER TABLE "message" ADD "is_forwarded" BOOL NOT NULL;
        ALTER TABLE "message" ADD "parse_mode" VARCHAR(50) NOT NULL;
        ALTER TABLE "message" ADD "origin_chat_id" INT NOT NULL;
        ALTER TABLE "message" ADD "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP;
        ALTER TABLE "message" DROP COLUMN "group_id";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ADD "group_id" VARCHAR(255) NOT NULL;
        ALTER TABLE "message" DROP COLUMN "telegram_message_id";
        ALTER TABLE "message" DROP COLUMN "is_forwarded";
        ALTER TABLE "message" DROP COLUMN "parse_mode";
        ALTER TABLE "message" DROP COLUMN "origin_chat_id";
        ALTER TABLE "message" DROP COLUMN "created_at";
        DROP TABLE IF EXISTS "broadcastrequest";
        ALTER TABLE "message" ADD CONSTRAINT "fk_message_group_b77d34e3" FOREIGN KEY ("group_id") REFERENCES "group" ("id") ON DELETE CASCADE;"""
