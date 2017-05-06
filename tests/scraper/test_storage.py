import io
import os
import py
import pytest
from scraper import storage


@pytest.fixture
def mock_storage(tmpdir: py._path.local.LocalPath) -> storage.Storage:
    return storage.MockStorage(os.path.join(tmpdir, 'storage'))


def test_mock_storage_returns_blob(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo')
    assert mock_blob.name() == 'foo'


def test_upload_download_string(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo/bar')
    data = "testing\n" \
           "\n" \
           "testing 123\n"
    mock_blob.upload_from_string(data)
    assert mock_blob.download_to_string() == data


def test_upload_from_file(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo/bar')
    data = io.BytesIO('testing'.encode('utf-8'))
    mock_blob.upload_from_file(data)
    assert mock_blob.download_to_string() == 'testing'


def test_download_to_file(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo/bar')
    mock_blob.upload_from_string('testing')
    output = io.BytesIO()
    mock_blob.download_to_file(output)
    output.seek(0)
    assert output.read().decode('utf-8') == 'testing'


def test_upload_from_filename(tmpdir: py._path.local.LocalPath, mock_storage: storage.Storage):
    filename = os.path.join(tmpdir, 'testing.txt')
    data = 'testing'
    with open(filename, 'w') as f:
        f.write(data)
    mock_blob = mock_storage.get_blob('foo/bar')
    mock_blob.upload_from_filename(filename)
    assert mock_blob.download_to_string() == data


def test_download_to_filename(tmpdir: py._path.local.LocalPath, mock_storage: storage.Storage):
    filename = os.path.join(tmpdir, 'testing.txt')
    data = 'testing'
    mock_blob = mock_storage.get_blob('foo/bar')
    mock_blob.upload_from_string(data)
    mock_blob.download_to_filename(filename)
    with open(filename) as f:
        assert f.read() == data


def test_exists(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo/bar')
    assert not mock_blob.exists()
    mock_blob.upload_from_string('testing')
    assert mock_blob.exists()


def test_delete(mock_storage: storage.Storage):
    mock_blob = mock_storage.get_blob('foo/bar')
    mock_blob.upload_from_string('testing')
    assert mock_blob.exists()
    mock_blob.delete()
    assert not mock_blob.exists()


def test_get_storage_not_production():
    assert os.environ.get('GITLAWCA') != 'production'
    st = storage.get_storage()
    assert isinstance(st, storage.MockStorage)

    mock_blob = st.get_blob('foo/bar/baz')
    mock_blob.upload_from_string('testing')
    assert mock_blob.download_to_string() == 'testing'
