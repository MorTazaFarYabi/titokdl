from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "referral" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "referrer_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "referred_id" VARCHAR(50) NOT NULL UNIQUE REFERENCES "user" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "source" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "identifier" VARCHAR(40) NOT NULL
);
        CREATE TABLE IF NOT EXISTS "sourceclick" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "source_id" INT NOT NULL REFERENCES "source" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sourceclick";
        DROP TABLE IF EXISTS "referral";
        DROP TABLE IF EXISTS "source";"""
