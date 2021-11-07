import copy
from typing import no_type_check

import jieba
import pangu
from bs4 import BeautifulSoup
from jinja2.filters import do_striptags
from slugify import slugify
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Router
from tortoise.exceptions import IntegrityError
from tortoise.functions import Count

from app.core.response import TemplateResponse
from app.models.posts import Post, Topic
from app.service.markdown import get_markdown
from app.service.readtime import read_time

router = Router()


async def index(request: Request) -> Response:
    topics = (
        await Topic.annotate(count_related_posts=Count("posts"))
        .all()
        .order_by("-count_related_posts")
    )
    topic = request.query_params.get("topic")
    if topic:
        posts = await Post.filter(topics__name__contains=topic).order_by("-timestamp")
    else:
        posts = await Post.all().order_by("-timestamp")
    return TemplateResponse(
        "pages/index.html",
        {"request": request, "posts": posts, "topics": topics, "topic": topic},
    )


@no_type_check
@requires("authenticated")
async def create_post(request: Request) -> RedirectResponse:
    form = await request.form()
    post = form["post_file"]
    title, _ = post.filename.split(".")
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
    topics = await Topic.all()
    seg = jieba.cut(soup.text)
    related_topics = [topic for topic in topics if topic.name in seg]
    post, _ = await Post.update_or_create(
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
    await post.topics.add(*related_topics)
    return RedirectResponse(url=request.url_for("post-get", slug=slug), status_code=303)


async def get_post(request: Request) -> Response:
    post = await Post.get_or_none(slug=request.path_params["slug"])
    if not post:
        raise HTTPException(status_code=404)
    return TemplateResponse("pages/post.html", {"request": request, "post": post})


@requires("authenticated")
async def create_topic(request: Request) -> RedirectResponse:
    form = await request.form()
    topic = form["topic"]
    try:
        await Topic.create(name=topic.capitalize())
    except IntegrityError:
        ...
    return RedirectResponse(url=request.url_for("index"), status_code=303)


@requires("authenticated")
async def delete_topic(request: Request) -> RedirectResponse:
    await Topic.filter(name=request.path_params["topic"]).delete()
    return RedirectResponse(url=request.url_for("index"), status_code=303)
