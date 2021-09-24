import logging
import sys
from pathlib import Path

from loguru import logger
from starlette.config import Config
from starlette.datastructures import Secret
from starlette.templating import Jinja2Templates

from app.core.logging import InterceptHandler

API_PREFIX = "/api"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

# database
DATABASE_URL: Secret = config("DATABASE_URL", cast=Secret)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)

# directory
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# logger
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access")

logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger("uvicorn").handlers = []
for logger_name in LOGGERS:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])
