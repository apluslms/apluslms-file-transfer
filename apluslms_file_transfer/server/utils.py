import os
import sys
import tarfile
from werkzeug.exceptions import HTTPException


def compare_files_to_update(manifest_client, manifest_srv):
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


# Upload handlers


def upload_octet_stream(file_data, temp_course_dir, file_index, chunk_index, last_chunk_flag):
    """ Download file data posted by a request with octet-stream content-type to the temp course directory
    """
    # parse data
    try:
        os.makedirs(temp_course_dir, exist_ok=True)

        # write the compressed file
        temp_compressed = os.path.join(temp_course_dir,
                                       'temp_' + file_index + '.tar.gz')

        with open(temp_compressed, 'ab') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            if chunk_index == str(file_size):
                f.write(file_data)

        if last_chunk_flag:  # The entire compressed file has been uploaded
            # extract the compressed file to a 'temp' dir
            with tarfile.open(temp_compressed, "r:gz") as tf:
                tf.extractall(temp_course_dir)

            os.remove(temp_compressed)  # Delete the compressed file
    except:
        raise


def upload_form_data(file, temp_course_dir):
    """ Upload file data posted by a request with form-data content-type to the temp course directory
    """
    try:
        # write the compressed file
        os.makedirs(temp_course_dir, exist_ok=True)
        temp_compressed = os.path.join(temp_course_dir, 'temp.tar.gz')
        with open(temp_compressed, 'wb') as f:
            chunk_size = 4096
            while True:
                chunk = file.stream.read(chunk_size)
                if len(chunk) == 0:
                    break
                f.write(chunk)

        # extract the compression file
        with tarfile.open(temp_compressed, "r:gz") as tf:
            tf.extractall(temp_course_dir)

        os.remove(temp_compressed)  # delete the compression file
    except:
        raise


# ----------------------------------------------------------------------------------------------------------------------
# Error handling

class ImproperlyConfigured(HTTPException):
    pass


def error_print():
    return '{}. {}, line: {}'.format(sys.exc_info()[0],
                                     sys.exc_info()[1],
                                     sys.exc_info()[2].tb_lineno)







