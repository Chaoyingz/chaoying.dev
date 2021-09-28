from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.api.routes import posts
from app.core import config

routes = [
    Route("/", endpoint=posts.index, name="index"),
    Route(
        "/upload_post", endpoint=posts.upload_post, methods=["POST"], name="upload_post"
    ),
    Route("/posts/{slug:str}", endpoint=posts.get_post, name="get_post"),
    Mount("/static", app=StaticFiles(directory=config.STATIC_DIR), name="static"),
]
