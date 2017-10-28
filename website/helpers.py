"""Collection of high-level helpers."""

from flask import Flask

from website.blog.helpers import create_articles


def setup_demo(app: Flask, item_count: int = 10) -> None:
    """Initialize a demo instance, with pre-written content.

    :param count: number of items to create for each website's component.
    """
    with app.app_context():
        create_articles(item_count)
