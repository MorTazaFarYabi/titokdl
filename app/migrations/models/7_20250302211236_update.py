from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sourceclick" ADD "user_id" VARCHAR(50) NOT NULL;
        ALTER TABLE "sourceclick" ADD CONSTRAINT "fk_sourcecl_user_9632ea58" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sourceclick" DROP CONSTRAINT "fk_sourcecl_user_9632ea58";
        ALTER TABLE "sourceclick" DROP COLUMN "user_id";"""
