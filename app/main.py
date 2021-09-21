from starlette.applications import Starlette

from app.api.routes.api import routes
from app.core.config import DEBUG
from app.core.events import create_start_app_handler


def get_application() -> Starlette:
    application = Starlette(debug=DEBUG, routes=routes)
    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_start_app_handler(application))
    return application


app = get_application()