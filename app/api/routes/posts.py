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
    description = do_striptags(soup.text)[:128]
    slug = slugify(title, max_length=64)
    read_time_text = read_time(body_html)
    topics = await Topic.all()
    for topic in topics:
        jieba.add_word(topic.name)
    seg = list(jieba.cut(soup.text))
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
    post = await Post.get_or_none(slug=request.path_params["slug"]).prefetch_related(
        "topics"
    )
    if not post:
        raise HTTPException(status_code=404)
    linked_post = {}
    if "（" in post.title:
        chinese_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
        numeral = post.title[-2]
        numeral_index = chinese_numerals.index(numeral)
        prev_title = post.title.replace(numeral, chinese_numerals[numeral_index - 1])
        next_title = post.title.replace(numeral, chinese_numerals[numeral_index + 1])
        if numeral_index > 0:
            linked_post["prev"] = await Post.get_or_none(title=prev_title)

        if numeral_index < 9:
            linked_post["next"] = await Post.get_or_none(title=next_title)

        if not linked_post.get("prev") and not linked_post.get("next"):
            linked_post = {}
    return TemplateResponse(
        "pages/post.html",
        {"request": request, "post": post, "linked_post": linked_post},
    )


@requires("authenticated")
async def create_topic(request: Request) -> RedirectResponse:
    form = await request.form()
    topic_name = form["topic"]
    try:
        topic = await Topic.create(name=topic_name.capitalize())
    except IntegrityError:
        ...
    else:
        posts = await Post.all()
        jieba.add_word(topic.name)
        for post in posts:
            soup = BeautifulSoup(post.body, "html.parser")
            seg = list(jieba.cut(soup.text))
            if topic.name in seg:
                await post.topics.add(topic)
    return RedirectResponse(url=request.url_for("index"), status_code=303)


@requires("authenticated")
async def delete_topic(request: Request) -> RedirectResponse:
    await Topic.filter(name=request.path_params["topic"]).delete()
    return RedirectResponse(url=request.url_for("index"), status_code=303)
