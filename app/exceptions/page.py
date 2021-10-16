from typing import Any

from starlette.requests import Request

from app.core.response import TemplateResponse


async def not_found(request: Request, _: Any) -> TemplateResponse:
    return TemplateResponse("404.html", {"request": request})


exception_handlers = {404: not_found}
