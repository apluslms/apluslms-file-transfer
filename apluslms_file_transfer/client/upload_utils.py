import os
from io import BytesIO
import tarfile
import requests
from math import floor
import logging

from apluslms_file_transfer.exceptions import UploadError
from apluslms_file_transfer.client.utils import tar_files_buffer, iter_read_chunks

logger = logging.getLogger(__name__)


def upload_files_by_tar(file_list, last_file, basedir, buff_size_threshold, upload_url, headers, data):
    """ Compress a list of files and then upload. The function is used to upload small files.

        If the buffer of the compression file smaller than buff_size_threshold, then it is upload.
        Otherwise the file list will be divided as two subsets.
        For each subset repeat the above process

    :param list list file_list: a list of uploaded files (tuple(file_path, file_size))
    :param str last_file: the path of the last file in the complete file_list
    :param str basedir: the base directory of the relative file path
    :param int|float buff_size_threshold: the threshold of buffer size to determine division action
    :param str upload_url: the url for uploading files
    :param dict headers: headers of requests
    :param dict data: data of requests
    """
    if not file_list:
        raise ValueError("The file list is empty!")

    # Generate the buffer of the compression file that contains the files in the file_list
    buffer = tar_files_buffer(file_list, basedir)

    buffer.seek(0, os.SEEK_END)
    pos = buffer.tell()
    # print('size of the buffer:', pos)
    # Change the stream position to the start
    buffer.seek(0)

    if pos <= buff_size_threshold or len(file_list) == 1:  # post the buffer
        files = {'file': buffer.getvalue()}
        data['last_file'] = (file_list[-1][0] == last_file)
        try:
            res = requests.post(upload_url, headers=headers, data=data, files=files)
            buffer.close()
        except:
            raise
        if res.status_code != 200:
            raise UploadError(res.text)

    else:  # Divide the file_list as two subsets and call the function for each subset
        file_sublists = [file_list[0:floor(len(file_list) / 2)], file_list[floor(len(file_list) / 2):]]
        for l in file_sublists:
            upload_files_by_tar(l, last_file, basedir, buff_size_threshold, upload_url, headers, data)


def upload_fbuffer_by_chunk(buffer, whether_last_file, upload_url, headers, data, file_index):
    """
    Upload a BytesIO buffer of a file by chunk. The function is used to upload big files.

    :param BytesIO object buffer: buffer to upload
    :param bool whether_last_file: whether the file is the last file to upload in this file employment process
    :param str upload_url: the url for uploading files
    :param dict headers: the headers in the request
    :param dict data: the data in the request
    :param int file_index: the index of the file in the (big) file list
    """
    chunk_size = 1024 * 1024 * 4
    index = 0
    for chunk, last_chunk in iter_read_chunks(buffer, chunk_size=chunk_size):
        offset = index + len(chunk)
        headers['Content-Type'] = 'application/octet-stream'
        headers['X-Process-ID'] = data['process_id']
        headers['X-Chunk-Size'] = str(chunk_size)
        headers['X-Chunk-Index'] = str(index)
        headers['X-Chunk-Offset'] = str(offset)
        headers['X-File-Index'] = str(file_index)
        if last_chunk:
            headers['X-Last-Chunk'] = 'True'
        if whether_last_file:
            headers['X-Last-File'] = 'True'
        index = offset
        try:
            res = requests.post(upload_url, headers=headers, data=chunk)
        except:
            raise
        if res.status_code != 200:
            raise UploadError(res.text)


def upload_files_to_server(files_and_sizes, basedir, upload_url, request_data):
    """
    Upload a collection of files to the server, using different uploading methods based on the fie size:

    1. the files bigger than 50MB are compressed one by one,
        and the smaller files are collected to fill a quota (50MB) and then compressed
    2. the compression file smaller than 4MB is posted directly, otherwise posted by chunks

    :param list files_and_sizes: a list of files to upload (tuple(file_path, file_size))
    :param basedir: the base directory of the relative file path
    :param upload_url: the url for uploading files
    :param dict request_data: the data in the request
    """
    # sub listing the files by their sizes (threshold = 50 MB)
    big_files = list(filter(lambda x: x[1] > 50.0 * (1024 * 1024), files_and_sizes))
    small_files = list(filter(lambda x: x[1] <= 50.0 * (1024 * 1024), files_and_sizes))

    init_headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }
    # big files are compressed and uploaded one by one
    if big_files:
        for file_index, f in enumerate(big_files):

            headers = init_headers
            last_file = (file_index == len(big_files) - 1 and not small_files)

            # Create the in-memory file-like object
            buffer = BytesIO()
            # Compress files
            try:
                with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
                    # Write the file to the in-memory tar
                    tf.add(f[0], os.path.relpath(f[0], start=basedir))
            except:
                raise

            # the current position of the buffer
            buffer.seek(0, os.SEEK_END)
            pos = buffer.tell()
            # print("length of the buffer: ", pos)
            # Change the stream position to the start
            buffer.seek(0)

            if pos <= 4.0 * (1024 * 1024):
                # upload the whole compressed file
                file = {'file': buffer.getvalue()}
                request_data['last_file'] = last_file
                try:
                    res = requests.post(upload_url, headers=headers, data=request_data, files=file)
                except:
                    raise
                if res.status_code != 200:
                    raise UploadError(res.text)

            else:   # Upload the compressed file by chunks
                upload_fbuffer_by_chunk(buffer, last_file, upload_url, init_headers, request_data, file_index)

            buffer.close()

    # Compress small files as one and post it
    if small_files:
        # Add the JWT token to the request headers for the authentication purpose
        headers = {
            'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
        }
        last_file = small_files[-1][0]

        upload_files_by_tar(small_files, last_file, basedir, 4 * 1024 * 1024, upload_url, headers, request_data)

