import markdown2
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Router

from app.core.config import config
from app.models.posts import Post

router = Router()


async def index(request: Request) -> JSONResponse:
    return config.templates.TemplateResponse("pages/index.html", {"request": request})


async def upload_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, ext = post.filename.split(".")
    body_md = await post.read()
    body_html = markdown2.markdown(body_md)
    await Post.create(title=title, body=body_html)
    return RedirectResponse(url=request.url_for("index"), status_code=303)
