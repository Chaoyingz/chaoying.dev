from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.url import routes
from app.core import config
from app.core.events import create_start_app_handler
from app.core.middleware import JWTAuthBackend
from app.exceptions.page import exception_handlers


def get_application() -> Starlette:
    middleware = [
        Middleware(SessionMiddleware, secret_key=config.SECRET_KEY),
        Middleware(
            AuthenticationMiddleware,
            backend=JWTAuthBackend(
                config.SECRET_KEY, algorithm=config.SECRET_ALGORITHM
            ),
        ),
    ]

    application = Starlette(
        debug=config.DEBUG,
        routes=routes,
        middleware=middleware,
        exception_handlers=exception_handlers,
    )
    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_start_app_handler(application))
    return application


app = get_application()
