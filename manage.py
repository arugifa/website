"""Used by Flask, to provide a command-line interface.

I don't use directly. I prefer Invoke,
because Invoke is more cool :ok_hand:
"""
from website.config import DevelopmentConfig
from website.helpers import create_app


app = create_app(DevelopmentConfig)
