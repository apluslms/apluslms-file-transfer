import logging
from functools import partial

import jwt
from werkzeug.exceptions import Unauthorized

from .utils import ImproperlyConfigured

logger = logging.getLogger(__name__)


def setting_in_bytes(app_instance, name):
    value = app_instance.config.get(name)
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode('utf-8')
    raise ImproperlyConfigured(
        "Value for settings.%s is not bytes or str."
        % (name,))


def prepare_decoder(app_instance):
    options = {'verify_' + k: True for k in ('iat', 'iss')}
    options.update({'require_' + k: True for k in ('iat',)})
    jwt_issuer = app_instance.config.get('JWT_ISSUER')
    if jwt_issuer:
        options['issuer'] = jwt_issuer

    if app_instance.config.get('JWT_PUBLIC_KEY'):
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
        except ImportError as error:
            raise ImproperlyConfigured(
                "Require `cryptography` when using settings.JWT_PUBLIC_KEY: %s"
                % (error,))
        pem = setting_in_bytes(app_instance, 'JWT_PUBLIC_KEY')
        try:
            key = load_pem_public_key(pem, backend=default_backend())
        except ValueError as error:
            raise ImproperlyConfigured(
                "Invalid public key in JWT_PUBLIC_KEY: %s"
                % (error,))
        return partial(jwt.decode,
                       key=key,
                       algorithms=app_instance.config.get('JWT_ALGORITHM'),
                       **options)
    return None


def jwt_auth(jwt_decode, authorization):

    if jwt_decode is None:
        raise ImproperlyConfigured(
            "Received request to %s without JWT_PUBLIC_KEY in settings."
            % (__name__,))

    try:
        scheme, token = authorization.strip().split(' ', 1)
        if scheme.lower() != 'bearer': raise ValueError()
    except ValueError:
        logger.debug("JWT auth failed: Invalid authorization header: %r",
                     authorization)
        raise Unauthorized("Invalid authorization header")

    # decode jwt token
    try:
        return jwt_decode(token)
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT auth failed: %s", exc)
        raise Unauthorized(str(exc))
