import markdown2
from slugify import slugify
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Router

from app.core.response import TemplateResponse
from app.models.posts import Post

router = Router()


async def index(request: Request) -> Response:
    posts = await Post.all()
    return TemplateResponse("pages/index.html", {"request": request, "posts": posts})


async def upload_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, ext = post.filename.split(".")
    body_md = await post.read()
    body_html = markdown2.markdown(body_md, extras=["fenced-code-blocks"])
    slug = slugify(title, max_length=64)
    await Post.create(title=title, body=body_html, slug=slug)
    return RedirectResponse(url=request.url_for("index"), status_code=303)


async def get_post(request: Request) -> Response:
    post = await Post.get_or_none(slug=request.path_params["slug"])
    return TemplateResponse("pages/post.html", {"request": request, "post": post})
