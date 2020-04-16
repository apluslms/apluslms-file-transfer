import os
import logging


from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest, convert_django_header

logger = logging.getLogger(__name__)


def upload_files(request, static_file_path, course_name):

    headers = {convert_django_header(k): v for k, v in request.META.items()}

    # upload/ update the courses files of a course
    try:
        if headers['content_type'] == 'application/octet-stream':

            process_id = headers['Process-ID']
            temp_course_dir = os.path.join(static_file_path, 'temp_' + course_name + '_' + process_id)

            file_data = request.body
            file_index = headers['File-Index']
            chunk_index = headers['Chunk-Index']
            last_chunk_flag = ('Last-Chunk' in request.headers)
            upload_octet_stream(temp_course_dir, file_data, file_index, chunk_index, last_chunk_flag)

            if 'Last-File' in headers:
                status = "completed"
                create_new_manifest(static_file_path, course_name, temp_course_dir)
            else:
                status = "in process - success"

        elif headers['content_type'].startswith('multipart/form-data'):

            data, file = request.POST, request.FILES['file']
            process_id = data['process_id']
            temp_course_dir = os.path.join(static_file_path, 'temp_' + course_name + '_' + process_id)
            upload_form_data(file, temp_course_dir)
            if data.get('last_file') is True or data.get('last_file') == 'True':
                status = "completed"
                create_new_manifest(static_file_path, course_name, temp_course_dir)
            else:
                status = "in process - success"
        else:
            raise ValueError('Upload-File Error: Unsupported content-type')
    except:
        raise

    return {"status": status}

