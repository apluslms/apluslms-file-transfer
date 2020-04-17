import logging

from flask import request

from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest, tempdir_path

logger = logging.getLogger(__name__)


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

