from sanic.exceptions import InvalidUsage
from sanic.request import Request

import auth


def validate_post_request(request: Request, fields: [str]) -> dict:
    '''
    Throws InvalidUsage exception if any given field is missing
    in the request body or URL arguments (in this order).
    '''
    error_message = 'Invalid request format. Mandatory fields are missing: {}'
    if not request.json and not request.args:
        raise InvalidUsage(error_message.format(repr(fields)))
    for source in [request.json, request.args]:
        if source:
            missing = [field for field in fields if field not in source]
            if len(missing):
                raise InvalidUsage(error_message.format(repr(missing)))
            else:
                return strip_list(source)


def strip_list(data: dict) -> dict:
    for k, v in data.items():
        data[k] = v if isinstance(v, str) else v[0]
    return data


def check_id(request, decoded):
    if request.app.captcha.is_issued(decoded['id']):
        request.app.captcha.remove_from_storage(decoded['id'])
        return (True, '')
    else:
        return (False, 'This captcha is already used')


def cleanup_fn(request, decoded):
    if 'id' in decoded:
        if request.app.captcha.is_issued(decoded['id']):
            request.app.captcha.remove_from_storage(decoded['id'])


def process_captcha(request: Request):
    '''
    This function must be used in places where captcha authentication is required.
    Captcha has to be either an entry of the request body
    {...'captcha': {'id': int, 'code': int}...}
    or a custom header of this format:
    'X-Captcha-Token: <value>', where value is a JWT-signed token.
    Throws InvalidUsage exception if provided captcha code is wrong, captcha token
    is invalid (e.g. it's forged and it doesn't pass sign check), the token is
    expired or there's no captcha provided at all.
    This function prioritizes the token from the headers over json data from
    the request body.
    After calling this function provided captcha is fully utilized and
    cannot be used again.

    '''
    if 'x-captcha-token' in request.headers:
        token = request.headers['x-captcha-token']
        result, reason = auth.verify_token(token, request,
                                           required_fields=['id'],
                                           verification_fn=check_id,
                                           exp_hook_fn=cleanup_fn)
        if not result:
            raise InvalidUsage(reason)
        else:
            return

    json = request.json
    if not json or 'captcha' not in json:
        return InvalidUsage('No CAPTCHA provided')
    elif 'id' not in json['captcha'] or 'code' not in json:
        return InvalidUsage('Wrong CAPTCHA object structure')
    else:
        if not request.app.captcha.check(json['captcha']['id'],
                                         json['captcha']['code']):
            raise InvalidUsage('Wrong CAPTCHA code')
