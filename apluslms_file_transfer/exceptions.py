import sys
from werkzeug.exceptions import HTTPException


class ImproperlyConfigured(HTTPException):
    pass


class EnvVarNotFoundError(Exception):
    def __init__(self, *var_name):
        self.msg = " & ".join(*var_name) + " missing!"

    def __str__(self):
        return repr(self.msg)


class GetFileUpdateError(Exception):
    pass


class UploadError(Exception):
    pass


class PublishError(Exception):
    pass


def error_print():
    return '{}. {}, line: {}'.format(sys.exc_info()[0],
                                     sys.exc_info()[1],
                                     sys.exc_info()[2].tb_lineno)
