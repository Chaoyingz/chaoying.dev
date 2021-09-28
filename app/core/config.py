import logging
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret
from starlette.templating import Jinja2Templates


class AppConfig:
    env = Config(".env")

    DEBUG: bool = env("DEBUG", cast=bool, default=False)

    # database
    DATABASE_URL: Secret = env("DATABASE_URL", cast=Secret)
    MAX_CONNECTIONS_COUNT: int = env("MAX_CONNECTIONS_COUNT", cast=int, default=10)
    MIN_CONNECTIONS_COUNT: int = env("MIN_CONNECTIONS_COUNT", cast=int, default=10)

    # directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATE_DIR = BASE_DIR / "templates"
    TEMPLATES = Jinja2Templates(directory=str(TEMPLATE_DIR))

    # logger
    LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO


config = AppConfig()
