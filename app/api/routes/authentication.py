from starlette.authentication import AuthenticationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core import config
from app.core.authentication import get_github_access_token, get_github_user


async def login(request: Request) -> RedirectResponse:
    try:
        code = request.query_params["code"]
    except KeyError:
        raise HTTPException(400, detail="`Code` parameter is required.")

    try:
        access_token = await get_github_access_token(code)
    except AuthenticationError as e:
        raise HTTPException(400, detail=str(e))

    try:
        user = await get_github_user(access_token)
    except AuthenticationError as e:
        raise HTTPException(400, detail=str(e))

    if user.upper() != config.GITHUB_USER.__str__().upper():
        raise HTTPException(400, detail=f"User {user} is not a blogger.")
    return RedirectResponse(url=request.url_for("homepage"), status_code=303)
