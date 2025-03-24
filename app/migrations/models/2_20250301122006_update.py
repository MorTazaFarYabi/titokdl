from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ADD "media_id" VARCHAR(100) NOT NULL  DEFAULT '';
        ALTER TABLE "message" ADD "media_url" TEXT NOT NULL;
        ALTER TABLE "message" ADD "media_type" VARCHAR(10) NOT NULL  DEFAULT '';
        ALTER TABLE "message" ALTER COLUMN "parse_mode" SET DEFAULT '';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" DROP COLUMN "media_id";
        ALTER TABLE "message" DROP COLUMN "media_url";
        ALTER TABLE "message" DROP COLUMN "media_type";
        ALTER TABLE "message" ALTER COLUMN "parse_mode" DROP DEFAULT;"""
