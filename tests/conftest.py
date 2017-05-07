import logging
import os
import subprocess
import psutil
import pytest
from google.cloud import datastore as google_datastore  # pylint:disable=import-error
from scraper import install

LOG = logging.getLogger('gitlawca')


@pytest.fixture(scope='session')
def datastore_service():
    LOG.info("Starting gcloud datastore emulator")
    system = install.get_platform()
    if not install.detect_gcloud(system):
        os.environ['PATH'] += os.path.pathsep + os.path.join(install.installation_folder(), 'google-cloud-sdk', 'bin')
    assert install.detect_gcloud(system)
    with psutil.Popen(['gcloud', 'beta', 'emulators', 'datastore', 'start', '--no-store-on-disk'],
                      stderr=subprocess.PIPE) as proc:
        try:
            while True:
                inline = proc.stderr.readline().decode('utf-8').strip()
                if 'export DATASTORE_EMULATOR_HOST=' in inline:
                    break

            _, address = inline.split('=')
            os.environ['DATASTORE_EMULATOR_HOST'] = address
            os.environ['DATASTORE_PROJECT_ID'] = 'gitlawca'

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
