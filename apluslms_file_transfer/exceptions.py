import sys
from werkzeug.exceptions import HTTPException


class ImproperlyConfigured(HTTPException):
    """Exception raised for improper configuration"""
    pass


class EnvVarNotFoundError(Exception):
    """Exception raised when the needed environment variables are not set"""
    def __init__(self, *var_name):
        self.msg = " & ".join(*var_name) + " missing!"

    def __str__(self):
        return repr(self.msg)


class GetFileUpdateError(Exception):
    """Exception raised during the process of getting files to update"""
    pass


class UploadError(Exception):
    """Exception raised during the process of uploading files"""
    pass


class PublishError(Exception):
    """Exception raised during the process of publishing files"""
    pass


def error_print():
    """Format of error printing"""
    return '{}. {}, line: {}'.format(sys.exc_info()[0],
                                     sys.exc_info()[1],
                                     sys.exc_info()[2].tb_lineno)
