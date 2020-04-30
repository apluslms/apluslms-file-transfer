import os
import tarfile


def upload_octet_stream(temp_course_dir, file_data, file_index, chunk_index, last_chunk_flag):
    """ Upload file data posted by a request with octet-stream content-type to the temp course directory.
    The data may be the complete content of the file or a part of the file.

    :param str temp_course_dir: the temporary directory that the file is uploaded to
    :param file_data: the content of the file data (chunk)
    :param int file_index: the index of the file in the uploaded file list
    :param int chunk_index: the index of the uploaded chunk of the file
    :param bool last_chunk_flag: the flag that indicates whether it is the last chunk of the file
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


def upload_form_data(file, temp_course_dir, framework='flask'):
    """ Upload file data posted by a request with form-data content-type to the temp course directory

    :param file: the content of the file
    :param str temp_course_dir: the temporary directory that the file is uploaded to
    :param str framework: the framework that the server is built by ('flask', 'django')
    """
    try:
        # write the compressed file
        os.makedirs(temp_course_dir, exist_ok=True)
        temp_compressed = os.path.join(temp_course_dir, 'temp.tar.gz')
        with open(temp_compressed, 'wb') as f:
            chunk_size = 4096
            if framework == 'flask':
                while True:
                    chunk = file.stream.read(chunk_size)
                    if len(chunk) == 0:
                        break
                    f.write(chunk)
            elif framework == 'django':
                for chunk in file.chunks():
                    f.write(chunk)
            else:
                raise ValueError("Unsupported framework")
        # extract the compression file
        with tarfile.open(temp_compressed, "r:gz") as tf:
            tf.extractall(temp_course_dir)

        os.remove(temp_compressed)  # delete the compression file
    except:
        raise
