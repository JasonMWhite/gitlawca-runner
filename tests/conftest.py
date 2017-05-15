import logging
import os
import subprocess
import psutil
import py  # pylint:disable=unused-import
import pytest
from google.cloud import datastore as google_datastore  # pylint:disable=import-error
from scraper import install
from scraper import storage

LOG = logging.getLogger('gitlawca')


@pytest.fixture(scope='session')
def datastore_service():
    system = install.get_platform()
    os.environ['CLOUDSDK_CORE_PROJECT'] = 'gitlawca'
    assert install.detect_gcloud(system)
    proc = psutil.Popen(['gcloud', 'beta', 'emulators', 'datastore', 'start',
                         '--no-store-on-disk', '--consistency=1.0'], stderr=subprocess.PIPE)
    try:
        while True:
            inline = proc.stderr.readline().decode('utf-8').strip()
            if 'export DATASTORE_EMULATOR_HOST=' in inline:
                break

        _, address = inline.split('=')
        os.environ['DATASTORE_EMULATOR_HOST'] = address
        os.environ['DATASTORE_PROJECT_ID'] = 'gitlawca'

        LOG.warning('Starting datastore emulated client at %s', address)
        yield google_datastore.Client('gitlawca')

        children = proc.children()
        while children:
            if children[0].name() == 'java':
                break
            children = children[0].children()
        if children:
            children[0].send_signal(subprocess.signal.SIGINT)
            LOG.info("Terminated gcloud datastore emulator")
        else:
            LOG.error("Could not find gcloud datastore emulator process to terminate")
    except subprocess.TimeoutExpired:
        LOG.error("timeout expired!")
        proc.kill()


@pytest.fixture
def datastore_client(datastore_service):
    assert 'DATASTORE_EMULATOR_HOST' in os.environ
    yield datastore_service

    query = datastore_service.query()
    query.keys_only()
    for row in query.fetch():
        datastore_service.delete(row.key)


@pytest.fixture
def stor(tmpdir: 'py.path.local') -> storage.Storage:
    os.environ['MOCK_STORAGE'] = str(tmpdir.join('gitlawca'))
    return storage.get_storage()
