import os
import sys
import json
import requests
import logging

from apluslms_file_transfer.client.utils import store_process_id
from apluslms_file_transfer.client.fileinfo import get_files_to_upload
from apluslms_file_transfer.client.upload_utils import upload_files_to_server
from apluslms_file_transfer.exceptions import PublishError, error_print


logger = logging.getLogger(__name__)


def upload(get_files_url, upload_url, init_headers, target_dir, pid_file):
    files_upload, process_id = get_files_to_upload(get_files_url, init_headers, target_dir)
    store_process_id(process_id, pid_file)
    try:
        data = {"process_id": process_id}
        upload_files_to_server(files_upload, target_dir, upload_url, data)
        print("The files are uploaded successfully")
    except Exception as e:
        print(str(e))
        sys.exit(1)


def publish(publish_url, init_headers, pid_file):
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
        print("The files are published successfully")
    except Exception as e:
        print(str(e))
        sys.exit(1)

