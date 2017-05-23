import logging
import os
import subprocess
import psutil
import py  # pylint:disable=unused-import
import pytest
from google.cloud import datastore as google_datastore  # pylint:disable=import-error
from google.cloud import pubsub  # pylint:disable=import-error
from scraper import install
from scraper import storage

LOG = logging.getLogger('gitlawca')


def terminate_subprocess(proc: psutil.Process, name: str):
    children = proc.children()
    while children:
        if children[0].name() == 'java':
            break
        children = children[0].children()
    if children:
        children[0].send_signal(psutil.signal.SIGINT)
        LOG.info("Terminated %s", name)
    else:
        LOG.error("Could not find java process to terminate for %s", name)


@pytest.fixture(scope='session')
def datastore_service():
    system = install.get_platform()
    os.environ['CLOUDSDK_CORE_PROJECT'] = 'gitlawca'
    assert install.detect_gcloud(system)
    proc = psutil.Popen(['gcloud', 'beta', 'emulators', 'datastore', 'start',
                         '--no-store-on-disk', '--consistency=1.0'], stderr=subprocess.PIPE)

    while True:
        inline = proc.stderr.readline().decode('utf-8').strip()
        if 'export DATASTORE_EMULATOR_HOST=' in inline:
            break

    _, address = inline.split('=')
    os.environ['DATASTORE_EMULATOR_HOST'] = address
    os.environ['DATASTORE_PROJECT_ID'] = 'gitlawca'

    LOG.warning('Starting datastore emulated client at %s', address)
    yield google_datastore.Client('gitlawca')

    terminate_subprocess(proc, "gcloud datastore emulator")


@pytest.fixture
def datastore_client(datastore_service):
    assert 'DATASTORE_EMULATOR_HOST' in os.environ
    yield datastore_service

    query = datastore_service.query()
    query.keys_only()
    for row in query.fetch():
        datastore_service.delete(row.key)


@pytest.fixture(scope='session')
def pubsub_service(tmpdir_factory) -> pubsub.Client:
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'gitlawca'
    pubsub_temp = tmpdir_factory.mktemp('pubsub')

    proc = psutil.Popen(['gcloud', 'beta', 'emulators', 'pubsub', 'start', '--data-dir={}'.format(str(pubsub_temp))],
                        stderr=subprocess.PIPE)
    while True:
        inline = proc.stderr.readline().decode('utf-8').strip()
        if 'Server started, listening on' in inline:
            break
    yield pubsub.Client('gitlawca')

    terminate_subprocess(proc, "gcloud pubsub emulator")


@pytest.fixture
def pubsub_client(pubsub_service: pubsub.Client) -> pubsub.Client:
    for sub in pubsub_service.list_subscriptions():
        sub.delete()

    for topic in pubsub_service.list_topics():
        topic.delete()

    yield pubsub_service

    for sub in pubsub_service.list_subscriptions():
        sub.delete()

    for topic in pubsub_service.list_topics():
        topic.delete()


@pytest.fixture
def stor(tmpdir: 'py.path.local') -> storage.Storage:
    os.environ['GITLAWCA'] = 'test'
    os.environ['MOCK_STORAGE'] = str(tmpdir.join('gitlawca'))
    return storage.get_storage()
