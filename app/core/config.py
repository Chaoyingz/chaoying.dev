import logging
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret


class AppConfig:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    ENV_FILE_PATH = BASE_DIR / ".env"
    env = Config(ENV_FILE_PATH)
    DEBUG = True

    ENVIRONMENT = env("ENVIRONMENT", default="default")

    # Auth
    SECRET_KEY: str = env("SECRET_KEY")
    SECRET_ALGORITHM: str = env("SECRET_ALGORITHM")
    TOKEN_KEY: str = "token"

    # Database
    POSTGRES_HOST: Secret = env("POSTGRES_HOST", cast=Secret)
    POSTGRES_USER: Secret = env("POSTGRES_USER", cast=Secret)
    POSTGRES_PASSWORD: Secret = env("POSTGRES_PASSWORD", cast=Secret)
    POSTGRES_DB: Secret = env("POSTGRES_DB", cast=Secret)

    DB_CONNECTION: Secret = f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
    DEV_DB_CONNECTION: Secret = env("DEV_DB_CONNECTION", cast=Secret)

    MAX_CONNECTIONS_COUNT: int = env("MAX_CONNECTIONS_COUNT", cast=int, default=10)
    MIN_CONNECTIONS_COUNT: int = env("MIN_CONNECTIONS_COUNT", cast=int, default=10)

    # Directory
    APP_DIR = BASE_DIR / "app"
    STATIC_DIR = APP_DIR / "static"
    TEMPLATE_DIR = APP_DIR / "templates"

    # logger
    LOGGING_LEVEL = logging.DEBUG

    # GITHUB
    GITHUB_CLIENT_ID: Secret = env("GITHUB_CLIENT_ID", cast=Secret)
    GITHUB_SECRET: Secret = env("GITHUB_SECRET", cast=Secret)
    GITHUB_USER: Secret = env("GITHUB_USER", cast=Secret)


class DevelopmentConfig(AppConfig):
    DB_CONNECTION = AppConfig.DEV_DB_CONNECTION


class ProductionConfig(AppConfig):
    DEBUG = False
    LOGGING_LEVEL = logging.WARNING


class TestingConfig(AppConfig):
    ...


ENVIRONMENT_MAPPING = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


config = ENVIRONMENT_MAPPING[AppConfig.ENVIRONMENT]


TORTOISE_ORM = {
    "connections": {"default": str(config.DB_CONNECTION)},
    "apps": {
        "models": {
            "models": ["app.models.posts", "app.models.users", "aerich.models"],
            "default_connection": "default",
        }
    },
}
