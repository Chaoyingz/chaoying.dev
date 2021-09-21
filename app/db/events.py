from loguru import logger
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from app.core.config import DATABASE_URL


async def connect_to_db(app: Starlette) -> None:
    logger.info("Connecting to database...")
    register_tortoise(
        app,
        db_url=str(DATABASE_URL),
        modules={"models": ["app.models.posts"]},
        generate_schemas=True,
    )
    logger.info("Connection established.")
