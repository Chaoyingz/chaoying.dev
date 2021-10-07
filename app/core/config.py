import logging
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

from app.core.templating import Jinja2Templates


class AppConfig:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    ENV_FILE_PATH = BASE_DIR / ".env"

    env = Config(ENV_FILE_PATH)

    DEBUG: bool = env("DEBUG", cast=bool, default=False)

    # Auth
    SECRET_KEY: str = env("SECRET_KEY")
    SECRET_ALGORITHM: str = env("SECRET_ALGORITHM")
    TOKEN_KEY: str = "token"

    # database
    DATABASE_URL: Secret = env("DATABASE_URL", cast=Secret)
    MAX_CONNECTIONS_COUNT: int = env("MAX_CONNECTIONS_COUNT", cast=int, default=10)
    MIN_CONNECTIONS_COUNT: int = env("MIN_CONNECTIONS_COUNT", cast=int, default=10)

    # directory
    APP_DIR = BASE_DIR / "app"
    STATIC_DIR = APP_DIR / "static"
    TEMPLATE_DIR = APP_DIR / "templates"
    TEMPLATES = Jinja2Templates(directory=str(TEMPLATE_DIR))

    # logger
    LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO

    # GITHUB
    GITHUB_CLIENT_ID: Secret = env("GITHUB_CLIENT_ID", cast=Secret)
    GITHUB_SECRET: Secret = env("GITHUB_SECRET", cast=Secret)
    GITHUB_USER: Secret = env("GITHUB_USER", cast=Secret)


config = AppConfig()
