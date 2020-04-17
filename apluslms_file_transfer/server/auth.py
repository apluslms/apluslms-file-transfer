import logging

import jwt
from werkzeug.exceptions import Unauthorized

logger = logging.getLogger(__name__)


def jwt_auth(jwt_decode, headers):

    try:
        # require authentication header
        authorization = headers.get('Authorization')
        if authorization is None:
            logger.debug("JWT auth failed: No authorization header")
            raise ValueError("JWT auth failed: No authorization header")
        scheme, token = authorization.strip().split(' ', 1)
        if scheme.lower() != 'bearer': raise ValueError("JWT auth failed: Invalid authorization header: %r",
                                                        authorization)
    except ValueError as exc:
        logger.error(exc)
        raise Unauthorized(str(exc))

    # decode jwt token
    try:
        return jwt_decode(token)
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT auth failed: %s", exc)
        raise Unauthorized(str(exc))


def authenticate(jwt_decode, headers, course_name):

    if course_name is None:
        raise Unauthorized('No valid course name provided')

    auth = jwt_auth(jwt_decode, headers)

    # check the payload
    if ('sub' not in auth) or (not auth['sub'].strip()):
        raise Unauthorized("Invalid payload")
    assert auth['sub'].strip() == course_name, 'the course name in the url does not match the jwt token'

    return auth

