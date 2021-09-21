from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Router

from app.models.posts import Post

router = Router()


@router.route("/")
async def index(_: Request) -> JSONResponse:
    posts = await Post.all()
    return JSONResponse({"posts": [str(post) for post in posts]})
