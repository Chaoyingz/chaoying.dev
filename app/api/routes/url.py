from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.api.routes import authentication, posts, sitemap
from app.core import config

routes = [
    Route("/", endpoint=posts.index, name="index"),
    Route(
        "/upload_post", endpoint=posts.upload_post, methods=["POST"], name="post-upload"
    ),
    Route("/posts/{slug:str}", endpoint=posts.get_post, name="post-get"),
    Route("/auth", endpoint=authentication.login, name="login"),
    Route("/logout", endpoint=authentication.logout, name="logout"),
    Mount("/static", app=StaticFiles(directory=config.STATIC_DIR), name="static"),
    Route("/sitemap.xml", sitemap.sitemap),
    Route("/robots.txt", sitemap.robots),
]
