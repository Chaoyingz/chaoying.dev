from starlette.routing import Mount

from app.api.routes import posts

routes = [Mount("/", routes=posts.router.routes)]
