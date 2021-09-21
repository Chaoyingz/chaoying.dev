from typing import Any, Callable

from loguru import logger
from starlette.applications import Starlette

from app.db.events import connect_to_db


def create_start_app_handler(app: Starlette) -> Callable[..., Any]:
    async def start_app() -> None:
        await connect_to_db(app)

    return start_app


def create_stop_app_handler(_: Starlette) -> Any:
    @logger.catch
    async def stop_app() -> None:
        ...

    return stop_app
