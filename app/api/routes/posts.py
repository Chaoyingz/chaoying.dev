from slugify import slugify
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Router

from app.core.response import TemplateResponse
from app.models.posts import Post
from app.service.markdown import markdown2html
from app.service.readtime import read_time

router = Router()


async def homepage(request: Request) -> Response:
    posts = await Post.all()
    return TemplateResponse("pages/homepage.html", {"request": request, "posts": posts})


@requires("authenticated")
async def upload_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, ext = post.filename.split(".")
    body_md = await post.read()
    body_html = markdown2html(body_md.decode("utf-8"))
    slug = slugify(title, max_length=64)
    read_time_text = read_time(body_html)
    await Post.create(title=title, body=body_html, slug=slug, read_time=read_time_text)
    return RedirectResponse(url=request.url_for("homepage"), status_code=303)


async def get_post(request: Request) -> Response:
    post = await Post.get_or_none(slug=request.path_params["slug"])
    return TemplateResponse("pages/post.html", {"request": request, "post": post})
