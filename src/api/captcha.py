from sanic import Blueprint
from sanic.response import json, raw

import auth
import util

captcha = Blueprint('captcha')


@captcha.route('/captcha', methods=['GET'], version=1)
async def get_captcha(request):
    img, id = request.app.captcha.get()
    return raw(img,
               content_type='image/png',
               headers={'content-disposition': 'inline; filename={}.png'.format(id)})


@captcha.route('/captcha', methods=['POST'], version=1)
async def post_captcha(request):
    data = util.validate_post_request(request, ['id', 'code'])
    if request.app.captcha.check(data['id'], data['code'], delete=False):
        status = 200
        body = {'token': await auth.issue_token(
            {'id': data['id']}, request.app.jwt_secret,
            exp_time=request.app.cfg.captcha_timeout)}
    else:
        status = 422
        body = {'error': 'Wrong CAPTCHA code'}
    return json(body, status=status)


@captcha.route('/captcha', methods=['PUT'], version=1)
async def utilize_captcha(request):
    util.process_captcha(request)
    return json({'status': 'ok'})
