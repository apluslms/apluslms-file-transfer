import os
from uuid import uuid4
from werkzeug.exceptions import BadRequest

from apluslms_file_transfer.server.utils import compare_files_to_update


def get_files_to_update(course_dir, manifest_client, manifest_srv, data, whether_can_renew):

    # if the course has not been uploaded yet, upload all the files
    if not os.path.exists(course_dir) or not os.path.isdir(course_dir):
        data['exist'] = False
        files_to_update = {'files_new': manifest_client,
                           'files_update': {},
                           'files_keep': {},
                           'files_remove': {}}
    # else if the course already exists
    else:
        if not whether_can_renew(manifest_srv, manifest_client):
            return BadRequest('Abort: the client version is older than server version')

        data['exist'] = True  # indicate the course exists in the server

        # compare the files between the client side and the server side
        # get list of files to upload / update
        files_to_update = compare_files_to_update(manifest_client, manifest_srv)

    # get a unique id for this uploading process
    process_id = str(uuid4())
    data['process_id'] = process_id

    return files_to_update, data
