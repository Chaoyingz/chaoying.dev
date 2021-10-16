from typing import List

import asgi_sitemaps
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import FileResponse

from app.core import config
from app.models.posts import Post


class StaticSitemap(asgi_sitemaps.Sitemap):
    async def items(self) -> List[str]:
        items = []
        request = Request(scope=self.scope)
        post_items = [
            URL(request.url_for("post-get", slug=post.slug)).path
            for post in await Post.all()
        ]
        static_route = ["index"]
        static_items = [URL(request.url_for(route)).path for route in static_route]
        items += post_items
        items += static_items
        return items

    def location(self, item: str) -> str:
        return item


sitemap = asgi_sitemaps.SitemapApp(StaticSitemap(), domain=config.DOMAIN)


async def robots(request: Request) -> FileResponse:
    path = config.BASE_DIR / "app" / "static" / "text" / "robots.txt"
    return FileResponse(path)
