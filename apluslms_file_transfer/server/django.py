import logging

from apluslms_file_transfer.server.upload_utils import upload_octet_stream, upload_form_data
from apluslms_file_transfer.server.utils import create_new_manifest, tempdir_path

logger = logging.getLogger(__name__)


def upload_files(request, upload_dir, course_name, res_data):

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


def convert_django_header(key):

    if key.startswith('HTTP_'):
        key = key.replace('HTTP_', '')

    return '-'.join(i.lower().capitalize() for i in key.split('_'))

