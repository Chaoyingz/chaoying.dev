from typing import Any

import markdown
from markdown.extensions.toc import TocExtension
from markdown_link_attr_modifier import LinkAttrModifierExtension
from slugify import slugify


def _slugify(value: str, *args: Any, **kwargs: Any) -> str:
    return slugify(value, max_length=64)


def markdown2html(body_md: str) -> str:
    body_html = markdown.markdown(
        body_md,
        extensions=[
            "fenced_code",
            "codehilite",
            TocExtension(slugify=_slugify, anchorlink=True),
            "attr_list",
            "markdown_captions",
            LinkAttrModifierExtension(
                new_tab="external_only", no_referrer="external_only", auto_title="on"
            ),
        ],
    )
    return body_html
