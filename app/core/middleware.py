from typing import Optional, Tuple, Union

import jwt
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
)
from starlette.requests import Request

from app.core import config


class JWTUser(BaseUser):
    def __init__(self, username: str, token: str, payload: dict) -> None:
        self.username = username
        self.token = token
        self.payload = payload

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username

    @property
    def identity(self) -> str:
        return ""


class JWTAuthBackend(AuthenticationBackend):
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        prefix: str = "JWT",
        username_field: str = "username",
        audience: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.prefix = prefix
        self.username_field = username_field
        self.audience = audience
        self.options = options or dict()

    async def authenticate(
        self, request: Request
    ) -> Union[None, Tuple[AuthCredentials, BaseUser]]:

        token = request.session.get(config.TOKEN_KEY)
        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                key=self.secret_key,
                algorithms=self.algorithm,
                audience=self.audience,
                options=self.options,
            )
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(str(e))

        return (
            AuthCredentials(["authenticated"]),
            JWTUser(
                username=payload[self.username_field], token=token, payload=payload
            ),
        )
