import markdown2
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Router

from app.core.config import config
from app.models.posts import Post

router = Router()


async def index(request: Request) -> Response:
    return config.templates.TemplateResponse("pages/index.html", {"request": request})


async def upload_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, ext = post.filename.split(".")
    body_md = await post.read()
    body_html = markdown2.markdown(body_md, extras=["fenced-code-blocks"])
    await Post.create(title=title, body=body_html)
    return RedirectResponse(url=request.url_for("index"), status_code=303)


async def get_post(request: Request) -> Response:
    post = await Post.get_or_none(id=request.path_params["post_id"])
    return config.templates.TemplateResponse(
        "pages/post.html", {"request": request, "post": post}
    )
