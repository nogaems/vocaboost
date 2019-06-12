from sanic.exceptions import InvalidUsage
from sanic.request import Request


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
