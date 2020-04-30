"""
Functions for the servers built using Django
"""
import logging
from functools import partial

import jwt
from django.conf import settings

from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest, tempdir_path
from apluslms_file_transfer.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def setting_in_bytes(name):
    """Get the configuration value of the server

    :param name: the name of the configuration
    :return: the value of the configuration
    :rtype: bytes
    """
    value = getattr(settings, name)
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode('utf-8')
    raise ImproperlyConfigured(
        "Value for settings.%s is not bytes or str."
        % (name,))


def prepare_decoder():
    """ Return the jwt decoder
    """
    options = {'verify_' + k: True for k in ('iat', 'iss')}
    options.update({'require_' + k: True for k in ('iat',)})
    if hasattr(settings, 'JWT_ISSUER'):
        options['issuer'] = settings.JWT_ISSUER

    if hasattr(settings, 'JWT_PUBLIC_KEY'):
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
        except ImportError as error:
            raise ImproperlyConfigured(
                "`mooc-grader api` requires `cryptography` when using settings.JWT_PUBLIC_KEY: %s"
                % (error,))
        pem = setting_in_bytes('JWT_PUBLIC_KEY')
        try:
            key = load_pem_public_key(pem, backend=default_backend())
        except ValueError as error:
            raise ImproperlyConfigured(
                "Invalid public key in JWT_PUBLIC_KEY: %s"
                % (error,))
        return partial(jwt.decode,
                       key=key,
                       algorithms=settings.JWT_ALGORITHM,
                       **options)
    return None


def convert_django_header(key):
    """Convert the key in the headers into a specific format

    :param str key: the key to convert in the headers
    :return: the converted key
    :rtype: str
    """

    if key.startswith('HTTP_'):
        key = key.replace('HTTP_', '')

    return '-'.join(i.lower().capitalize() for i in key.split('_'))


def upload_files(request, upload_dir, course_name, res_data):
    """Upload the files in the posted request to the server

    :param str upload_dir: the directory path where the course directory located
    :param str course_name: the name of the course
    :param res_data: the initial dictionary containing info to send back to the client
    :return: the dictionary that contains the manifest of the updated files to send back to the client
    :rtype: dict
    """

    headers = {convert_django_header(k): v for k, v in request.META.items()}

    # upload/ update the courses files of a course
    try:
        if headers['Content-Type'] == 'application/octet-stream':

            pid = headers['X-Process-ID']

            temp_course_dir = tempdir_path(upload_dir, course_name, pid)
            upload_octet_stream(temp_course_dir=temp_course_dir,
                                file_data=request.body,
                                file_index=request.headers['X-File-Index'],
                                chunk_index=request.headers['X-Chunk-Index'],
                                last_chunk_flag='X-Last-Chunk' in headers)

            if 'X-Last-File' in headers:
                res_data['status'] = "completed"
                create_new_manifest(upload_dir, course_name, temp_course_dir)
            else:
                res_data['status'] = "in process - success"

        elif headers['Content-Type'].startswith('multipart/form-data'):

            request_data, file = request.POST, request.FILES['file']
            pid = request_data['process_id']
            temp_course_dir = tempdir_path(upload_dir, course_name, pid)

            upload_form_data(file, temp_course_dir, framework='django')

            if request_data.get('last_file') is True or request_data.get('last_file') == 'True':
                res_data['status'] = "completed"
                create_new_manifest(upload_dir, course_name, temp_course_dir)
            else:
                res_data['status'] = "in process - success"
        else:
            raise ValueError('Upload-File Error: Unsupported content-type')
    except:
        raise

    return res_data




