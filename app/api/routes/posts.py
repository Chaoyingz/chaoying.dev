import copy
from typing import no_type_check

import pangu
from bs4 import BeautifulSoup
from jinja2.filters import do_striptags
from slugify import slugify
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Router

from app.core.response import TemplateResponse
from app.models.posts import Post
from app.service.markdown import get_markdown
from app.service.readtime import read_time

router = Router()


async def index(request: Request) -> Response:
    posts = await Post.all().order_by("-timestamp")
    return TemplateResponse("pages/index.html", {"request": request, "posts": posts})


@no_type_check
@requires("authenticated")
async def upload_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, ext = post.filename.split(".")
    body_md = await post.read()
    markdown = get_markdown()
    body_html = markdown.convert(body_md.decode("utf-8"))
    body_html_pangu = pangu.spacing_text(body_html)
    soup = BeautifulSoup(body_html_pangu, "html.parser")
    source_element = soup.find("p", {"id": "source"})
    if source_element:
        source = copy.copy(source_element)
        source_element.decompose()
    else:
        source = None
    description = do_striptags(body_html)[:128]
    slug = slugify(title, max_length=64)
    read_time_text = read_time(body_html)
    await Post.update_or_create(
        title=title,
        defaults=dict(
            body=soup,
            toc=markdown.toc,
            source=source,
            description=description,
            slug=slug,
            read_time=read_time_text,
        ),
    )
    return RedirectResponse(url=request.url_for("post-get", slug=slug), status_code=303)


async def get_post(request: Request) -> Response:
    post = await Post.get_or_none(slug=request.path_params["slug"])
    if not post:
        raise HTTPException(status_code=404)
    return TemplateResponse("pages/post.html", {"request": request, "post": post})
