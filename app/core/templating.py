import jinja2
from starlette import templating

from app.core import config


class Jinja2Templates(templating.Jinja2Templates):
    def get_env(self, directory: str) -> "jinja2.Environment":
        env: "jinja2.Environment" = super().get_env(directory)
        env.globals["GITHUB_CLIENT_ID"] = config.GITHUB_CLIENT_ID
        return env
