import abc
import random
import os
import sys
import typing
from google.cloud import storage  # pylint:disable=import-error


class Blob(metaclass=abc.ABCMeta):
    def name(self) -> str:
        pass

    def exists(self) -> bool:
        pass

    def delete(self) -> None:
        pass

    def upload_from_file(self, file: typing.IO[typing.Any]) -> None:
        pass

    def upload_from_filename(self, filename: str) -> None:
        pass

    def upload_from_string(self, data: str) -> None:
        pass

    def download_to_file(self, file: typing.IO[typing.Any]) -> None:
        pass

    def download_to_filename(self, filename: str) -> None:
        pass

    def download_to_string(self) -> str:
        pass


class Storage(metaclass=abc.ABCMeta):
    def get_blob(self, blob_name: str) -> Blob:
        pass


class MockBlob(Blob):
    def __init__(self, base_path: str, name: str) -> None:
        self.__name = name
        self.__path = os.path.join(base_path, name)

    def name(self) -> str:
        return self.__name

    def exists(self) -> bool:
        return os.path.exists(self.__path)

    def delete(self) -> None:
        assert os.path.exists(self.__path)
        os.remove(self.__path)

    def upload_from_file(self, file: typing.IO[typing.Any]) -> None:
        dirname = os.path.dirname(self.__path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.__path, 'wb') as f:
            f.write(file.read())

    def upload_from_filename(self, filename: str) -> None:
        with open(filename, 'rb') as f:
            self.upload_from_file(f)

    def upload_from_string(self, data: str) -> None:
        dirname = os.path.dirname(self.__path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.__path, 'w') as f:
            f.write(data)

    def download_to_file(self, file: typing.IO[typing.Any]) -> None:
        with open(self.__path, 'rb') as f:
            file.write(f.read())

    def download_to_filename(self, filename: str) -> None:
        with open(filename, 'wb') as f:
            self.download_to_file(f)

    def download_to_string(self) -> str:
        with open(self.__path) as f:
            return f.read()


class MockStorage(Storage):
    def __init__(self, path: str) -> None:
        self.__path = path

    def get_blob(self, blob_name: str):
        return MockBlob(self.__path, blob_name)


class GoogleBlob(Blob):
    def __init__(self, blob_name: str, blob: storage.blob.Blob) -> None:
        self.__blob = blob
        self.__blob_name = blob_name

    def name(self) -> str:
        return self.__blob_name

    def exists(self) -> bool:
        return self.__blob.exists()

    def delete(self) -> None:
        self.__blob.delete()

    def upload_from_file(self, file: typing.IO[typing.Any]) -> None:
        self.__blob.upload_from_file(file)

    def upload_from_filename(self, filename: str) -> None:
        self.__blob.upload_from_filename(filename)

    def upload_from_string(self, data: str) -> None:
        self.__blob.upload_from_string(data)

    def download_to_file(self, file: typing.IO[typing.Any]) -> None:
        self.__blob.download_to_file(file)

    def download_to_filename(self, filename: str) -> None:
        return self.__blob.download_to_filename(filename)

    def download_to_string(self) -> str:
        return self.__blob.download_as_string().decode('utf-8')


class GoogleStorage(Storage):
    def __init__(self, bucket: storage.Bucket) -> None:
        self.__bucket = bucket

    def get_blob(self, blob_name: str):
        return GoogleBlob(blob_name, self.__bucket.get_blob(blob_name))


def get_storage() -> Storage:
    if os.environ.get('GITLAWCA') == 'production':
        stor = storage.Client('gitlawca')
        return GoogleStorage(stor.get_bucket('gitlawca.appspot.com'))
    else:
        temp_path = os.path.join('/tmp/gitlawca', str(random.randint(1, sys.maxsize)))
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        return MockStorage(temp_path)
