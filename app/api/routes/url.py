from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.api.routes import posts
from app.core.config import STATIC_DIR

routes = [
    Route("/", endpoint=posts.index, name="index"),
    Route(
        "/upload_post", endpoint=posts.upload_post, methods=["POST"], name="upload_post"
    ),
    Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static"),
]
