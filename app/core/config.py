import logging
import sys

from loguru import logger
from starlette.config import Config
from starlette.datastructures import Secret

from app.core.logging import InterceptHandler

API_PREFIX = "/api"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

DATABASE_URL: Secret = config("DATABASE_URL", cast=Secret)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)


# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access")

logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger("uvicorn").handlers = []
for logger_name in LOGGERS:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])
