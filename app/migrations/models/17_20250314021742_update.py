from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "forcedjoinrecord" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_joined_in_all" BOOL NOT NULL  DEFAULT False,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
        ALTER TABLE "message" ALTER COLUMN "reply_markup_type" SET DEFAULT 'I';
        CREATE TABLE IF NOT EXISTS "transactions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "currency_type" VARCHAR(2) NOT NULL,
    "reason" VARCHAR(2) NOT NULL,
    "amount" INT NOT NULL,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
        ALTER TABLE "userbalance" ADD "user_id" VARCHAR(50) NOT NULL UNIQUE;
        ALTER TABLE "userbalance" ADD "gem" INT NOT NULL  DEFAULT 0;
        ALTER TABLE "userbalance" ADD "gold_coin" INT NOT NULL  DEFAULT 500;
        CREATE TABLE "forcedjoinrecord_forcedjoinchannelorder" (
    "forcedjoinchannelorder_id" INT NOT NULL REFERENCES "forcedjoinchannelorder" ("id") ON DELETE CASCADE,
    "forcedjoinrecord_id" INT NOT NULL REFERENCES "forcedjoinrecord" ("id") ON DELETE CASCADE
);
        CREATE UNIQUE INDEX "uid_userbalance_user_id_9d85da" ON "userbalance" ("user_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "forcedjoinrecord_forcedjoinchannelorder";
        DROP INDEX "uid_userbalance_user_id_9d85da";
        ALTER TABLE "message" ALTER COLUMN "reply_markup_type" DROP DEFAULT;
        ALTER TABLE "userbalance" DROP COLUMN "user_id";
        ALTER TABLE "userbalance" DROP COLUMN "gem";
        ALTER TABLE "userbalance" DROP COLUMN "gold_coin";
        DROP TABLE IF EXISTS "forcedjoinrecord";
        DROP TABLE IF EXISTS "transactions";"""
