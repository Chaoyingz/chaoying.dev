import logging
import sys
from types import FrameType
from typing import cast

from loguru import logger

from app.core import config


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


async def init_logger() -> None:
    LOGGERS = ("uvicorn.asgi", "uvicorn.access")

    logging.getLogger().handlers = [InterceptHandler()]
    logging.getLogger("uvicorn").handlers = []
    for logger_name in LOGGERS:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler(level=config.LOGGING_LEVEL)]

    logger.configure(handlers=[{"sink": sys.stderr, "level": config.LOGGING_LEVEL}])
