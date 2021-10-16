from starlette.authentication import AuthenticationError, requires
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core import config
from app.core.authentication import generate_token
from app.service.github import get_github_access_token, get_github_user


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

    token = generate_token(user)
    request.session[config.TOKEN_KEY] = token
    return RedirectResponse(url=request.url_for("index"), status_code=303)


@requires("authenticated")
async def logout(request: Request) -> RedirectResponse:
    request.session.pop(config.TOKEN_KEY)
    return RedirectResponse(url=request.url_for("index"), status_code=303)
