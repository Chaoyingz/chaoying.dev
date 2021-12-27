from typing import Any

import markdown
from markdown import Markdown
from markdown.extensions.toc import TocExtension
from markdown_link_attr_modifier import LinkAttrModifierExtension
from slugify import slugify


def _slugify(value: str, *args: Any, **kwargs: Any) -> str:
    return slugify(value, max_length=64)


def get_markdown() -> Markdown:
    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "codehilite",
            TocExtension(slugify=_slugify, permalink="", toc_depth=3),
            "markdown_captions",
            "attr_list",
            LinkAttrModifierExtension(
                new_tab="external_only", no_referrer="external_only", auto_title="on"
            ),
            "pymdownx.tilde",
            "pymdownx.highlight",
        ]
    )
    return md
