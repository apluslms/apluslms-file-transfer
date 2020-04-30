import os
import sys
import json
import requests
import logging

from apluslms_file_transfer.client.utils import store_process_id
from apluslms_file_transfer.client.fileinfo import get_files_to_upload
from apluslms_file_transfer.client.upload_utils import upload_files_to_server
from apluslms_file_transfer.exceptions import PublishError
from apluslms_file_transfer.color_print import PrintColor

logger = logging.getLogger(__name__)


def upload(get_files_url, upload_url, init_headers, target_dir, pid_file):
    """
    Select and then upload files to the server

    :param str get_files_url: the url sent to the server to get the updated files
    :param str upload_url: the url sent to the server to upload files
    :param dict init_headers: the initial headers in the request being sent
    :param str target_dir: the path of the local directory to upload
    :param str pid_file: the local file path that stores the process id of the file deployment process
    """
    try:
        PrintColor.info("Selecting files to upload...")
        files_upload, process_id = get_files_to_upload(get_files_url, init_headers, target_dir)
        store_process_id(process_id, pid_file)
        data = {"process_id": process_id}
        PrintColor.info("Uploading selected files...")
        upload_files_to_server(files_upload, target_dir, upload_url, data)
    except Exception as e:
        PrintColor.err(str(e))
        sys.exit(1)


def publish(publish_url, init_headers, pid_file):
    """
    Publish uploaded files into use

    :param str publish_url:  the url sent to the server to publish files
    :param dict init_headers: the initial headers in the request being sent
    :param str pid_file: the local file path that stores the process id of the file deployment process
    """
    PrintColor.info("Publishing files...")
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
    except Exception as e:
        PrintColor.err(str(e))
        sys.exit(1)

