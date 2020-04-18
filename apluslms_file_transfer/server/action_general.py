import os
import json
from uuid import uuid4
import logging
import shutil
import threading

from filelock import FileLock

from apluslms_file_transfer.server.utils import (get_update_files,
                                                 whether_allow_renew,
                                                 tempdir_path,)
from apluslms_file_transfer.exceptions import (GetFileUpdateError,
                                               PublishError,
                                               error_print,)

logger = logging.getLogger(__name__)


def files_to_update(upload_dir, course_name, upload_file_type, manifest_client, data):

    course_dir = os.path.join(upload_dir, course_name)
    # if the course has not been uploaded yet, upload all the files
    if not os.path.exists(course_dir) or not os.path.isdir(course_dir):
        data['exist'] = False
        files_update = {'files_new': manifest_client,
                        'files_update': {},
                        'files_keep': {},
                        'files_remove': {}}
    # else if the course already exists
    else:
        with open(os.path.join(course_dir, 'manifest.json'), 'r') as manifest_srv_file:
            manifest_srv = json.load(manifest_srv_file)

        if not whether_allow_renew(manifest_srv, manifest_client, upload_file_type):
            raise GetFileUpdateError('Abort: the client version is older than server version')

        data['exist'] = True  # indicate the course exists in the server

        # compare the files between the client side and the server side
        # get list of files to upload / update
        files_update = get_update_files(manifest_srv, manifest_client)

    # get a unique process id for this uploading process
    process_id = str(uuid4())
    data['process_id'] = process_id

    # create a temp directory where the files will be uploaded to
    temp_dir = tempdir_path(upload_dir, course_name, process_id)
    os.mkdir(temp_dir)
    # Store the files will be updated in a temp json file
    with open(os.path.join(temp_dir, 'files_to_update.json'), 'w') as f:
        # f.write(json.dumps(files_to_update, sort_keys=True, indent=4))
        json.dump(files_update, f, sort_keys=True, indent=4)
    data['files_new'], data['files_update'] = files_update['files_new'], files_update['files_update']

    return data


def publish_files(upload_dir, course_name, file_type, temp_course_dir, res_data):
    # if the course does exist, rename the temp dir

    course_dir = os.path.join(upload_dir, course_name)
    if not os.path.exists(course_dir):
        os.rename(temp_course_dir, course_dir)
    # if the course already exist
    else:
        manifest_srv_file = os.path.join(course_dir, 'manifest.json')
        manifest_client_file = os.path.join(temp_course_dir, 'manifest.json')
        lock_f = os.path.join(upload_dir, course_name + '.lock')
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


def start_cleanup(static_path, cleanup_time):

    def cleanup():
        dirs = next(os.walk(static_path))[1]
        for temp_dir in [d for d in dirs if d.startswith('temp')]:
            shutil.rmtree(os.path.join(static_path, temp_dir))

        # Set the next thread to happen
        global cleanup_thread
        cleanup_thread = threading.Timer(cleanup_time, cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

    global cleanup_thread
    cleanup_thread = threading.Timer(cleanup_time, cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()

