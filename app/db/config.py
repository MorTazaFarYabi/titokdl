
from tortoise import Tortoise, connections
from tortoise.log import logger
from config import Config, TORTOISE_ORM

async def start_db():
    await Tortoise.init(config=TORTOISE_ORM)
    # await Tortoise.init(
    #         db_url=Config.DB_URL,
    #         modules={'models': ['db.models']}
    #     )
    logger.info("Tortoise-ORM started, %s, %s", connections._get_storage(), Tortoise.apps)
    # logger.info("Tortoise-ORM generating schema")
    # await Tortoise.generate_schemas()

async def close_db():
    await connections.close_all()
    logger.info("Tortoise-ORM shutdown")