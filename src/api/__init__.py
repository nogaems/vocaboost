from sanic import Blueprint
from sanic.response import text

from .login import login
from .captcha import captcha

api = Blueprint.group(login, captcha, url_prefix='/api')
