from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "apireq" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "service_provider" VARCHAR(50) NOT NULL,
    "url" TEXT NOT NULL,
    "parameters" TEXT NOT NULL,
    "status" INT NOT NULL,
    "response" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "forcedjoinchannelorder" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "channel_id" VARCHAR(255) NOT NULL  DEFAULT '',
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(255) NOT NULL,
    "link" VARCHAR(255) NOT NULL,
    "is_fake_force" BOOL NOT NULL  DEFAULT False,
    "number_of_ordered_members" INT NOT NULL  DEFAULT 0,
    "completion_status" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "hdprofilepicinfo" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "instagramaccount" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "username" VARCHAR(60) NOT NULL UNIQUE,
    "bio" TEXT,
    "full_name" VARCHAR(150),
    "type" VARCHAR(10) NOT NULL,
    "profile" TEXT NOT NULL,
    "profile_hd" TEXT NOT NULL,
    "posts" INT NOT NULL,
    "followers" INT NOT NULL,
    "following" INT NOT NULL,
    "is_verified" BOOL NOT NULL,
    "is_business" BOOL NOT NULL
);
CREATE TABLE IF NOT EXISTS "mediaitem" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "link" TEXT NOT NULL,
    "type" VARCHAR(255) NOT NULL,
    "uploader_insta_account" VARCHAR(255) NOT NULL,
    "data_extracted_from_one_api" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "settings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "max_forced_channels" INT NOT NULL  DEFAULT 3,
    "default_language" VARCHAR(255) NOT NULL  DEFAULT 'fa',
    "is_bot_active" BOOL NOT NULL  DEFAULT True,
    "cache_times" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "subscriptionplan" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL,
    "permitted_downloads" JSONB NOT NULL,
    "request_per_second_limit" INT NOT NULL,
    "does_see_forced_joins" BOOL NOT NULL,
    "default_plan" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(255) NOT NULL,
    "last_name" VARCHAR(255) NOT NULL,
    "is_bot" BOOL NOT NULL  DEFAULT False,
    "state" TEXT NOT NULL,
    "role" VARCHAR(1) NOT NULL  DEFAULT 'N',
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "last_interaction_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "has_blocked_the_bot" BOOL NOT NULL  DEFAULT False,
    "has_started" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "bot" (
    "bot_token" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "admin_id" VARCHAR(50) REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "channel" (
    "id" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_bot_admin" BOOL NOT NULL  DEFAULT True,
    "is_comment_active" BOOL NOT NULL  DEFAULT True,
    "admin_id" VARCHAR(50) REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "channelmembership" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "joined_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "left_at" TIMESTAMPTZ,
    "joined_from" VARCHAR(10) NOT NULL,
    "joined_from_link" VARCHAR(100),
    "channel_id" VARCHAR(255) NOT NULL REFERENCES "channel" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "channelmembership" IS 'everytime sb join a channel an instance of this object will be inserted into the database';
CREATE TABLE IF NOT EXISTS "group" (
    "id" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_bot_admin" BOOL NOT NULL  DEFAULT True,
    "is_comment_active" BOOL NOT NULL  DEFAULT True,
    "admin_id" VARCHAR(50) REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "instagramrequest" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "request_type" VARCHAR(255) NOT NULL,
    "request_status" INT NOT NULL,
    "parameters" JSONB NOT NULL,
    "api_request_id" INT NOT NULL REFERENCES "apireq" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "message" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "group_id" VARCHAR(255) NOT NULL REFERENCES "group" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "usersubscriptionplan" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "ends_at" TIMESTAMPTZ NOT NULL,
    "subscription_plan_id" INT NOT NULL REFERENCES "subscriptionplan" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(50) NOT NULL UNIQUE REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "mediaitem_user" (
    "mediaitem_id" INT NOT NULL REFERENCES "mediaitem" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
