import os
import sys
import traceback
from io import BytesIO
import json
import requests
import logging

from aplus_file_management.client.fileinfo import get_files_manifest_in_folder
from aplus_file_management.client.utils import (store_process_id,
                                                GetFileUpdateError,
                                                PublishError,
                                                error_print,
                                                )
from aplus_file_management.client.upload import upload_files_to_server

logger = logging.getLogger(__name__)


def get_files_to_upload(url, headers, target_dir):
    manifest = get_files_manifest_in_folder(target_dir)
    buffer = BytesIO()
    buffer.write(json.dumps(manifest).encode('utf-8'))
    buffer.seek(0)

    try:
        get_files_r = requests.post(url, headers=headers,
                                    files={"manifest_client": buffer.getvalue()})
        if get_files_r.status_code != 200:
            raise GetFileUpdateError(get_files_r.text)

        if not get_files_r.json().get("exist"):
            # upload the whole folder if the course not exist in the server yet
            # print("The course {} will be newly added".format(os.environ['PLUGIN_COURSE']))
            files_upload = [(target_dir, os.path.getsize(target_dir))]
        else:
            # else get the files to add/update
            # print("The course {} already exists, will be updated".format(os.environ['PLUGIN_COURSE']))
            files_new = get_files_r.json().get("files_new")
            files_update = get_files_r.json().get("files_update")

            files_upload_dict = {**files_new, **files_update}
            files_upload = list()
            for f in list(files_upload_dict.keys()):
                full_path = os.path.join(target_dir, f)
                file_size = os.path.getsize(full_path)
                files_upload.append((full_path, file_size))

        pid = get_files_r.json().get("process_id")
    except:
        logger.error(traceback.format_exc())
        sys.exit(1)

    return files_upload, pid


def client_action_upload(get_files_url, upload_url, init_headers, target_dir, pid_file):
    files_upload, pid = get_files_to_upload(get_files_url, init_headers, target_dir)
    store_process_id(pid, pid_file)
    try:
        # 2. upload files
        data = {"process_id": pid}
        upload_files_to_server(files_upload, target_dir, upload_url, data)
    except:
        print(error_print())
        sys.exit(1)


def client_action_publish(publish_url, init_headers, pid_file):
    try:
        with open(pid_file, 'r') as f:
            process_id = json.load(f)['process_id']
        data = {"process_id": process_id}
        init_headers["Content-Type"] = "application/json"
        try:
            os.remove(pid_file)
        except:
            pass
        finalizer_r = requests.get(publish_url, headers=init_headers, json=data)
        if finalizer_r.status_code != 200:
            raise PublishError(finalizer_r.text)
        print("The course is published")
    except:
        print(error_print())
        sys.exit(1)

