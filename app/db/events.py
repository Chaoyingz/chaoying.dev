from loguru import logger
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from app.core.config import TORTOISE_ORM


async def connect_to_db(app: Starlette) -> None:
    logger.info("Connecting to database...")
    register_tortoise(app, config=TORTOISE_ORM, generate_schemas=True)
    logger.info("Connection established.")
