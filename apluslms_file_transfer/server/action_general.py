import os
import json
from uuid import uuid4
import logging
import shutil

from filelock import FileLock

from apluslms_file_transfer.server.utils import (get_update_files,
                                                 whether_allow_renew,
                                                 error_print,)
from apluslms_file_transfer.exceptions import GetFileUpdateError, PublishError

logger = logging.getLogger(__name__)


def files_to_update(static_file_path, course_name, manifest_client, data):

    course_dir = os.path.join(static_file_path, course_name)
    # if the course has not been uploaded yet, upload all the files
    if not os.path.exists(course_dir) or not os.path.isdir(course_dir):
        data['exist'] = False
        files_update = {'files_new': manifest_client,
                        'files_update': {},
                        'files_keep': {},
                        'files_remove': {}}
    # else if the course already exists
    else:
        with open(os.path.join(static_file_path, course_name, 'manifest.json'), 'r') as manifest_srv_file:
            manifest_srv = json.load(manifest_srv_file)

        if not whether_allow_renew(manifest_srv, manifest_client):
            raise GetFileUpdateError('Abort: the client version is older than server version')

        data['exist'] = True  # indicate the course exists in the server

        # compare the files between the client side and the server side
        # get list of files to upload / update
        files_update = get_update_files(manifest_srv, manifest_client)

    # get a unique id for this uploading process
    process_id = str(uuid4())
    data['process_id'] = process_id

    # create a temp directory where the files will be uploaded to
    temp_dir = os.path.join(static_file_path, 'temp_' + course_name + '_' + process_id)
    os.mkdir(temp_dir)
    # Store the files will be updated in a temp json file
    with open(os.path.join(temp_dir, 'files_to_update.json'), 'w') as f:
        # f.write(json.dumps(files_to_update, sort_keys=True, indent=4))
        json.dump(files_update, f, sort_keys=True, indent=4)
    data['files_new'], data['files_update'] = files_update['files_new'], files_update['files_update']

    return data


# def upload_files(static_file_path, course_name, framework='flask'):
#     if framework == 'flask':
#         from flask import request
#         content_type = request.content_type
#     elif framework == 'django':
#         meta = request.META


def publish_files(static_file_path, course_name, file_type, temp_course_dir, res_data):
    # if the course does exist, rename the temp dir

    course_dir = os.path.join(static_file_path, course_name)
    if not os.path.exists(course_dir):
        os.rename(temp_course_dir, course_dir)
    # if the course already exist
    else:
        manifest_srv_file = os.path.join(course_dir, 'manifest.json')
        manifest_client_file = os.path.join(temp_course_dir, 'manifest.json')
        lock_f = os.path.join(static_file_path, course_name + '.lock')
        lock = FileLock(lock_f)
        try:
            with open(manifest_client_file, 'r') as f:
                manifest_client = json.load(f)
            with lock.acquire(timeout=1):
                with open(manifest_srv_file, 'r') as f:
                    manifest_srv = json.load(f)

            if not whether_allow_renew(manifest_srv, manifest_client, file_type):
                return PublishError('Abort: the client version is older than server version')

            os.rename(course_dir, course_dir + '_old')
            os.rename(temp_course_dir, course_dir)
            shutil.rmtree(course_dir + '_old')
            os.remove(lock_f)
        except:
            logger.debug(error_print())
            os.remove(lock_f)
            raise PublishError(error_print())

    res_data['msg'] = 'The course is successfully uploaded'
    return res_data

