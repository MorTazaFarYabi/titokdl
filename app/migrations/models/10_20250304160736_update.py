from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
       
        ALTER TABLE "user" ADD "is_from_accepter" BOOL NOT NULL  DEFAULT False;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "is_from_accepter";
        ALTER TABLE "dynamiccommand" ALTER COLUMN "extra_actions" DROP DEFAULT;"""
