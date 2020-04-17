import logging
from functools import partial

import jwt
from flask import request

from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest, tempdir_path
from apluslms_file_transfer.exceptions import ImproperlyConfigured

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


def upload_files(upload_dir, course_name, res_data):

    content_type = request.content_type

    # upload/ update the courses files of a course
    try:
        if content_type == 'application/octet-stream':

            pid = request.headers['X-Process-ID']

            temp_course_dir = tempdir_path(upload_dir, course_name, pid)
            upload_octet_stream(temp_course_dir=temp_course_dir,
                                file_data=request.data,
                                file_index=request.headers['X-File-Index'],
                                chunk_index=request.headers['X-Chunk-Index'],
                                last_chunk_flag='X-Last-Chunk' in request.headers)

            if 'X-Last-File' in request.headers:
                res_data['status'] = "completed"
                create_new_manifest(upload_dir, course_name, temp_course_dir)
            else:
                res_data['status'] = "in process - success"

        elif content_type.startswith('multipart/form-data'):

            request_data, file = request.form, request.files['file']
            pid = request_data['process_id']
            temp_course_dir = tempdir_path(upload_dir, course_name, pid)

            upload_form_data(file, temp_course_dir)

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

