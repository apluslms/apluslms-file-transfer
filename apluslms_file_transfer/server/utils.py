import os
import json
import logging

from filelock import FileLock

from apluslms_file_transfer import FILE_TYPE1
from apluslms_file_transfer.exceptions import error_print

logger = logging.getLogger(__name__)


def get_update_files(manifest_srv, manifest_client):
    """ Get list of the files to update
    :param manifest_client: a nested dict dict[file] = {'size': , 'mtime': } in the client-side (a specific course)
    :param manifest_srv: a nested dict dict[file] = {'size': , 'mtime': } in the server side
    :return:
            a nested dict containing the files of newly added, updated and removed
    """
    if not isinstance(manifest_client, dict) or not isinstance(manifest_srv, dict):
        raise TypeError("The manifest is not a dict type")

    client_files, srv_files = set(manifest_client.keys()), set(manifest_srv.keys())

    files_remove = list(srv_files - client_files)
    files_new = {f: manifest_client[f] for f in list(client_files - srv_files)}

    files_inter = client_files.intersection(srv_files)
    files_replace = {f: manifest_client[f] for f in files_inter
                     if manifest_client[f]["mtime"] > manifest_srv[f]["mtime"]}
    files_keep = list(files_inter - set(files_replace.keys()))

    files_to_update = {'files_new': files_new,
                       'files_update': files_replace,
                       'files_keep': files_keep,
                       'files_remove': files_remove}

    return files_to_update


def whether_allow_renew(manifest_srv, manifest_client, file_type):

    if file_type in FILE_TYPE1:
        # check whether the index mtime is earlier than the one in the server
        index_key = "index.{}".format(file_type)
        flag = manifest_client[index_key]['mtime'] > manifest_srv[index_key]['mtime']
    else:
        latest_mtime_srv = max(file['mtime'] for file in manifest_srv.values())
        latest_mtime_client = max(file['mtime'] for file in manifest_client.values())
        flag = latest_mtime_client > latest_mtime_srv

    return flag


def create_new_manifest(static_file_path, course_name, temp_course_dir):
    with open(os.path.join(temp_course_dir, 'files_to_update.json'), 'r') as f:
        files_to_update = json.loads(f.read())

    files_new, files_update, files_keep, files_remove = (files_to_update['files_new'],
                                                         files_to_update['files_update'],
                                                         files_to_update['files_keep'],
                                                         files_to_update['files_remove'])
    os.remove(os.path.join(temp_course_dir, 'files_to_update.json'))

    course_dir = os.path.join(static_file_path, course_name)

    if not os.path.exists(course_dir) and not files_update and not files_keep and not files_remove:
        with open(os.path.join(temp_course_dir, 'manifest.json'), 'w') as f:
            json.dump(files_new, f)
    else:
        manifest_file = os.path.join(static_file_path, course_name, 'manifest.json')
        lock_f = os.path.join(static_file_path, course_name + '.lock')
        lock = FileLock(lock_f)
        try:
            with lock.acquire(timeout=1):
                with open(manifest_file, 'r') as f:
                    manifest_srv = json.load(f)

            for f in files_keep:
                temp_fp = os.path.join(temp_course_dir, f)
                os.makedirs(os.path.dirname(temp_fp), exist_ok=True)
                os.link(os.path.join(course_dir, f), temp_fp)

            # add/update manifest
            files_upload = {**files_new, **files_update}
            for f in files_upload:
                manifest_srv[f] = files_upload[f]
            # remove old files
            for f in files_remove:
                del manifest_srv[f]

            with open(os.path.join(temp_course_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest_srv, f)
            os.remove(lock_f)
        except:
            logger.debug(error_print())
            os.remove(lock_f)
            raise


def tempdir_path(upload_dir, course_name, pid):

    return os.path.join(upload_dir, 'temp_' + course_name + '_' + pid)














