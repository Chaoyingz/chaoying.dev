import aiohttp
from loguru import logger
from starlette.authentication import AuthenticationError

from app.core import config

GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


async def get_github_access_token(code: str) -> str:
    url = (
        f"{GITHUB_ACCESS_TOKEN_URL}?client_id={config.GITHUB_CLIENT_ID}&client_secret={config.GITHUB_SECRET}"
        f"&code={code}"
    )
    headers = {"Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            json_body = await resp.json()
            try:
                access_token: str = json_body["access_token"]
            except KeyError:
                logger.debug(f"Get github access token failed, {json_body=}.")
                raise AuthenticationError(json_body.get("error_description"))
    return access_token


async def get_github_user(access_token: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(GITHUB_USER_URL, headers=headers) as resp:
            json_body = await resp.json()
        try:
            user: str = json_body["login"]
        except KeyError:
            logger.debug(f"Get github user failed, {json_body=}.")
            raise AuthenticationError(json_body.get("error_description"))
    return user
