import logging
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret
from starlette.templating import Jinja2Templates


class AppConfig:
    _config = Config(".env")

    api_prefix = "/api"

    debug: bool = _config("DEBUG", cast=bool, default=False)

    # database
    database_url: Secret = _config("DATABASE_URL", cast=Secret)
    max_connections_count: int = _config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
    min_connections_count: int = _config("MIN_CONNECTIONS_COUNT", cast=int, default=10)

    # directory
    base_dir = Path(__file__).resolve().parent.parent
    static_dir = base_dir / "static"
    template_dir = base_dir / "templates"
    templates = Jinja2Templates(directory=str(template_dir))

    # logger
    logging_level = logging.DEBUG if debug else logging.INFO


config = AppConfig()
