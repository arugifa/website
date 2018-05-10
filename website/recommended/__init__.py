from flask import Blueprint

recommended = Blueprint('recommended', __name__, template_folder='templates')

from . import views  # noqa: E402, F401
