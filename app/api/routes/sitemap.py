import inspect
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

import asgi_sitemaps
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import FileResponse

from app.core import config
from app.models.posts import Post


@dataclass
class Item:
    url: str
    lastmod: Optional[datetime]


class StaticSitemap(asgi_sitemaps.Sitemap):
    def __init__(self) -> None:
        super().__init__()
        self.request: Request
        self.item_func_prefix = "get_item"

    def _get_path(self, name: str, **kwargs: Any) -> str:
        path: str = URL(self.request.url_for(name, **kwargs)).path
        return path

    async def get_item_static_page(self) -> AsyncGenerator[Item, None]:
        route_names = ["index"]
        for name in route_names:
            yield Item(url=self._get_path(name), lastmod=None)

    async def get_item_post(self) -> AsyncGenerator[Item, None]:
        for post in await Post.all():
            yield Item(
                url=self._get_path("post-get", slug=post.slug), lastmod=post.updated_at
            )

    async def items(self) -> AsyncGenerator[Item, None]:
        self.request = Request(scope=self.scope)  # noqa
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith(self.item_func_prefix):
                async for item in func():
                    yield item

    def location(self, item: Item) -> str:
        return item.url

    def lastmod(self, item: Item) -> Optional[datetime]:
        return item.lastmod

    def changefreq(self, item: Item) -> str:
        return "always"


sitemap = asgi_sitemaps.SitemapApp(StaticSitemap(), domain=config.DOMAIN)


async def robots(request: Request) -> FileResponse:
    path = config.BASE_DIR / "app" / "static" / "text" / "robots.txt"
    return FileResponse(path)
