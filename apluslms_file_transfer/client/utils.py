import os
from io import BytesIO
import tarfile
import json

from apluslms_file_transfer import FILE_TYPE1
from apluslms_file_transfer.exceptions import EnvVarNotFoundError


def read_in_chunks(buffer, chunk_size=1024 * 1024.0 * 4):
    """Read a buffer in chunks

    Arguments:
        buffer -- a BytesIO object

    Keyword Arguments:
        chunk_size {float} -- the chunk size of each read (default: {1024*1024*4})
    """
    while True:
        data = buffer.read1(chunk_size)
        if not data:
            break
        yield data


def iter_read_chunks(buffer, chunk_size=1024 * 1024 * 4):
    """a iterator of read_in_chunks function

    Arguments:
        buffer -- a BytesIO object

    Keyword Arguments:
         chunk_size {float} -- the chunk size of each read (default: {1024*1024*4})
    """
    # Ensure it's an iterator and get the first field
    it = iter(read_in_chunks(buffer, chunk_size))
    prev = next(read_in_chunks(buffer, chunk_size))
    for item in it:
        # Lag by one item so I know I'm not at the end
        yield prev, False
        prev = item
    # Last item
    yield prev, True


def tar_files_buffer(files, basedir):
    """generate a buffer of a compression file

    :param files: a list of tuples (file_path, file_size)
    :param basedir: str, the base directory of the relative file path
    :return: a BytesIO object
    """
    # Create the in-memory file-like object
    buffer = BytesIO()

    # Create the in-memory file-like object
    with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
        for index, f in enumerate(files):
            # Add the file to the tar file
            # 1. 'add' method
            tf.add(f[0], os.path.relpath(f[0], start=basedir))
            # 2. 'addfile' method
            # tf.addfile(tarfile.TarInfo(file_name),open(f[0],'rb'))

    # Change the stream position to the start
    buffer.seek(0)
    return buffer


def store_process_id(process_id, file):
    """store the id of this process
    """
    with open(file, 'w') as f:
        json.dump({'process_id': process_id}, f)


def examine_env_var():
    required = {'PLUGIN_API', 'PLUGIN_TOKEN', 'PLUGIN_COURSE'}

    if required <= os.environ.keys():
        pass
    else:
        missing = [var for var in required if var not in os.environ]
        raise EnvVarNotFoundError(missing)


def validate_directory(directory, file_type):
    """ Check whether the static directory and the index.html file exist
    :param directory: str, the path of a static directory
    :param file_type: str, the file type to upload ('html', 'yaml')
    :return: the path of the static directory, the path of the index.html file
             and the modification time of the index.html
    """
    if file_type in FILE_TYPE1:
        # The path of the subdirectory that contains static files
        target_dir = os.path.join(directory, '_build', file_type)
        index_file = os.path.join(target_dir, 'index.' + file_type)
        if not os.path.exists(target_dir):
            raise FileNotFoundError("_build/{} directory not found".format(file_type))
        elif not os.path.isdir(target_dir):
            raise NotADirectoryError("'_build/{}' is not a directory".format(file_type))
        elif not os.path.exists(index_file):
            raise FileNotFoundError("index.{} not found".format(file_type))

        return {"target_dir": target_dir}
    else:
        # for future possible file types
        # now raise a ValueError
        raise ValueError("Unsupported file types")


