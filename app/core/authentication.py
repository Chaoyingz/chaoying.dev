import jwt

from app.core import config


def generate_token(username: str) -> str:
    token = jwt.encode(
        dict(username=username), config.SECRET_KEY, algorithm=config.SECRET_ALGORITHM
    )
    return str(token)
