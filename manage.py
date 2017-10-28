"""Used by Flask, to provide a command-line interface.

I don't use directly. I prefer Invoke, because Invoke is more cool :ok_hand:
"""
from website import create_app
from website.config import DevelopmentConfig


app = create_app(DevelopmentConfig)
