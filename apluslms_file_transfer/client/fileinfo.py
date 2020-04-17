import os
import json
import requests
from io import BytesIO
from hashlib import sha256
import logging

from apluslms_file_transfer.exceptions import GetFileUpdateError, error_print

logger = logging.getLogger(__name__)


def get_manifest(file):

    st = os.stat(file)
    return {"mtime": st.st_mtime_ns,
            "checksum": 'sha256:' + sha256(open(file, 'rb').read()).hexdigest()}


def get_files_manifest_in_folder(directory):
    """
    get manifest of files
    :param directory: str, the path of the directory
    :return: a nested dict with rel_file_name as the key and the value is a dict holding the file mtime and the size
    """
    # IGNORE = set(['.git', '.idea', '__pycache__'])  # or NONIGNORE if the dir/file starting with '.' is ignored

    manifest = dict()

    for basedir, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        files = [f for f in files if not f.startswith('.')]
        for filename in files:
            file = os.path.join(basedir, filename)
            file_manifest = get_manifest(file)
            file_name = os.path.relpath(file, start=directory)
            manifest[file_name] = file_manifest

    return manifest


def get_files_to_upload(url, headers, target_dir):
    """

    :param url: str
    :param headers: dict
    :param target_dir: str
    :return:
        files_upload: a list of tuple (file_path, file_size)
        pid: a str process_id
    """
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

        process_id = get_files_r.json().get("process_id")
    except:
        raise

    return files_upload, process_id

