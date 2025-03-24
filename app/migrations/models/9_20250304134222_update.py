from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "dynamiccommand" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "command_name" VARCHAR(100) NOT NULL,
    "extra_actions" JSONB NOT NULL
);
        CREATE TABLE "dynamiccommand_message" (
    "message_id" INT NOT NULL REFERENCES "message" ("id") ON DELETE CASCADE,
    "dynamiccommand_id" INT NOT NULL REFERENCES "dynamiccommand" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "dynamiccommand_message";
        DROP TABLE IF EXISTS "dynamiccommand";"""
