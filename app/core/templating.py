import jinja2
from starlette import templating


class Jinja2Templates(templating.Jinja2Templates):
    def get_env(self, directory: str) -> "jinja2.Environment":
        env: "jinja2.Environment" = super().get_env(directory)

        return env
