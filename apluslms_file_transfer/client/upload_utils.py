import os
from io import BytesIO
import tarfile
import requests
from math import floor
import logging

from apluslms_file_transfer.exceptions import UploadError
from apluslms_file_transfer.client.utils import (tar_files_buffer,
                                                 iter_read_chunks,
                                                 )

logger = logging.getLogger(__name__)


def upload_files_by_tar(file_list, last_file, basedir, buff_size_threshold, upload_url, headers, data):
    """ Compress a list of files and upload.
        If the buffer of the compression file smaller than buff_size_threshold, uploaded.
        Otherwise the file list will be divided as two subsets.
        For each subset repeat the above process

    :param file_list: a list of tuples (file_path, file_size)
    :param last_file: str, the path of the last file in the complete file_list
    :param basedir: str, the base directory of the relative file path
    :param buff_size_threshold: float, the threshold of buffer size to determine division action
    :param upload_url: api url for uploading files
    :param headers: dict, headers of requests
    :param data: dict, data of requests
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
    upload a BytesIO buffer of a file by chunk
    :param BytesIO object buffer:
    :param bool whether_last_file:
    :param str upload_url:
    :param dict headers:
    :param dict data:
    :param int file_index:
    :return:
    """
    chunk_size = 1024 * 1024 * 4
    index = 0
    for chunk, last_chunk in iter_read_chunks(buffer, chunk_size=chunk_size):
        offset = index + len(chunk)
        headers['Content-Type'] = 'application/octet-stream'
        headers['Process-ID'] = data['process_id']
        headers['Chunk-Size'] = str(chunk_size)
        headers['Chunk-Index'] = str(index)
        headers['Chunk-Offset'] = str(offset)
        headers['File-Index'] = str(file_index)
        if last_chunk:
            headers['Last-Chunk'] = 'True'
        if whether_last_file:
            headers['Last-File'] = 'True'
        index = offset
        try:
            res = requests.post(upload_url, headers=headers, data=chunk)
        except:
            raise
        if res.status_code != 200:
            raise UploadError(res.text)


def upload_files_to_server(files_and_sizes, basedir, upload_url, data):
    """
    1. the files bigger than 50MB are compressed one by one,
        and the smaller files are collected to fill a quota (50MB) and then compressed
    2. the compression file smaller than 4MB is posted directly, otherwise posted by chunks

    :param files_and_sizes:
    :param basedir:
    :param upload_url:
    :param data:
    :return:
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
                data['last_file'] = last_file
                try:
                    res = requests.post(upload_url, headers=headers, data=data, files=file)
                except:
                    raise
                if res.status_code != 200:
                    raise UploadError(res.text)

            else:   # Upload the compressed file by chunks
                upload_fbuffer_by_chunk(buffer, last_file, upload_url, init_headers, data, file_index)

            buffer.close()

    # Compress small files as one and post it
    if small_files:
        # Add the JWT token to the request headers for the authentication purpose
        headers = {
            'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
        }
        last_file = small_files[-1][0]

        upload_files_by_tar(small_files, last_file, basedir, 4 * 1024 * 1024, upload_url, headers, data)

