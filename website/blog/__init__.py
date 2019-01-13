from flask import Blueprint

blog = Blueprint('blog', __name__, template_folder='templates')

from website.blog import views  # noqa: E402, F401
