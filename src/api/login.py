from sanic import Blueprint
from sanic.response import json, text
from sanic.exceptions import InvalidUsage, Unauthorized

import auth
import model
import util

login = Blueprint('login')


@login.route('/login', methods=['POST'], version=1)
async def login_handler(request):
    data = util.validate_post_request(request, ['username', 'password'])
    user = request.app.session.query(
        model.User).filter_by(username=data['username']).first()
    # Mitigation of time-attack
    user = user if user else model.User('', '')
    if auth.check_password(data['password'], user.password, user.salt):
        token = await auth.issue_token(user.username, request.app.jwt_secret)
        return json({'token': token})
    else:
        raise Unauthorized('Wrong username or password')
