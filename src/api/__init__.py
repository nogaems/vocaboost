from sanic import Blueprint
from sanic.response import text

from .login import login

api = Blueprint.group(login, url_prefix='/api')
