import os
import logging

from flask import request

from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest

logger = logging.getLogger(__name__)


def upload_files(static_file_path, course_name, res_data):

    content_type = request.content_type

    # upload/ update the courses files of a course
    try:
        if content_type == 'application/octet-stream':

            process_id = request.headers['Process-ID']
            file_index = request.headers['File-Index']
            chunk_index = request.headers['Chunk-Index']
            last_chunk_flag = ('Last-Chunk' in request.headers)
            file_data = request.data

            temp_course_dir = os.path.join(static_file_path, 'temp_' + course_name + '_' + process_id)
            upload_octet_stream(temp_course_dir, file_data, file_index, chunk_index, last_chunk_flag)

            if 'Last-File' in request.headers:
                res_data['status'] = "completed"
                create_new_manifest(static_file_path, course_name, temp_course_dir)
            else:
                res_data['status'] = "in process - success"

        elif content_type.startswith('multipart/form-data'):

            data, file = request.form, request.files['file']
            process_id = data['process_id']
            temp_course_dir = os.path.join(static_file_path, 'temp_' + course_name + '_' + process_id)

            upload_form_data(file, temp_course_dir)

            if data.get('last_file') is True or data.get('last_file') == 'True':
                res_data['status'] = "completed"
                create_new_manifest(static_file_path, course_name, temp_course_dir)
            else:
                res_data['status'] = "in process - success"
        else:
            raise ValueError('Upload-File Error: Unsupported content-type')
    except:
        raise

    return res_data

