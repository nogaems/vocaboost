from sanic.request import Request
from argon2 import argon2_hash
from secrets import token_hex
from hashlib import sha256
from sanic.exceptions import Unauthorized
from jwt.exceptions import ExpiredSignatureError
import jwt

import datetime
from typing import Callable, Tuple
from functools import wraps
import re

import model

# Since I'm using JWT with the HS256 hashing algorithm, 256 bits (32 bytes) is enough
salt_length = jwt_secret_length = 32


def hashed_password(password: str, salt: str = None) -> (str, str):
    '''
    Prepares typed-in password to be dumped to the db. Basically it's just:
    sha256(sha256(password) + salt) with some sort of permutations.
    I'm not considering using of the pepper thing because of its several flaws that
    make it pretty much useless. Read more at https://stackoverflow.com/a/16896216
    '''
    salt = salt if salt else token_hex(salt_length)
    return (argon2_hash(password, salt).hex(), salt)


async def issue_token(data: dict, secret: str, exp_time: int = 3600) -> str:
    '''
    Using JSON Web Token algorithm signs up the payload of a token being issued
    with the secret, that makes it impossible to forge or modify the token contents.
    The secret is a random sequence of bytes that is the same for every user
    and being set when sanic starts.
    You could think of it as a environment variable.
    It is possible to specify the life time of a token in seconds with exp_time.
    Default value is an hour.
    '''
    payload = {'exp': datetime.datetime.utcnow(
    ) + datetime.timedelta(seconds=exp_time)}
    payload.update(data)
    return jwt.encode(payload, secret).decode('utf8')


async def check_user(request, decoded):
    user = await request.app.session.query(model.User).filter_by(username=decoded['sub']).first()
    if not user:
        return (False, 'Token subject doesn\'t exist')
    else:
        return (True, '')


def exp_hook_fn(request, decoded):
    pass


def verify_token(token: str, request: Request,
                 required_fields: [str] = ['sub'],
                 verification_fn:
                 Callable[[Request, dict],
                          Tuple[bool, str]] = check_user,
                 exp_hook_fn:
                 Callable[[Request, dict], None] = exp_hook_fn) -> (bool, str):
    '''
    Returns (True, '') if a token passes varification,
    otherwise returns (False, "Reason").
    '''
    if token == '':
        return (False, 'Token is missing')
    try:
        token = token.encode('utf8')
    except UnicodeEncodeError as e:
        return (False, e.reason)

    try:
        decoded = jwt.decode(token, request.app.jwt_secret)
    except ExpiredSignatureError as e:
        decoded = jwt.decode(token.request.app.jwt_secret, verify=False)
        exp_hook_fn(request, decoded)
        return (False, 'Token has expired')
    except jwt.PyJWTError as e:
        return (False, e.args[0])

    missing = [field for field in required_fields if field not in decoded]
    if missing:
        return (False, f'Token fields are missing: {repr(missing)}')

    result, reason = verification_fn(request, decoded)
    return (result, reason)


def check_password(typed: str, hashed: str, salt: str) -> bool:
    return hashed == hashed_password(typed, salt=salt)[0]


def get_token(request) -> str:
    if 'Authorization' in request.headers:
        result = re.findall('Bearer ([\w\._-]+)',
                            request.headers['Authorization'])
        if len(result) == 1:
            return result[0]
    return ''


def auth_required(handler=None):
    @wraps(handler)
    async def wrapper(request, *args, **kwargs):
        auth = await verify_token(get_token(request), request)
        if not auth[0]:
            raise Unauthorized(
                "Authentication error: {}".format(auth[1]))
        return await handler(request, *args, **kwargs)

    return wrapper
