import logging
import os
import psutil
import pytest
import subprocess
from google.cloud import datastore as google_datastore

LOG = logging.getLogger('gitlawca')


@pytest.fixture(scope='module')
def datastore_client():
    LOG.info("Starting gcloud datastore emulator")
    p = psutil.Popen(['gcloud', 'beta', 'emulators', 'datastore', 'start', '--no-store-on-disk'], stderr=subprocess.PIPE)

    while True:
        inline = p.stderr.readline().decode('utf-8').strip()
        if 'export DATASTORE_EMULATOR_HOST=' in inline:
            break

    _, address = inline.split('=')
    os.environ['DATASTORE_EMULATOR_HOST'] = address
    os.environ['DATASTORE_PROJECT_ID'] = 'gitlawca'

    ds = google_datastore.Client('gitlawca')
    yield ds

    children = p.children()
    while children:
        if children[0].name() == 'java':
            break
        children = children[0].children()
    if children:
        children[0].send_signal(subprocess.signal.SIGINT)
        LOG.info("Terminated gcloud datastore emulator")
    else:
        LOG.error("Could not find gcloud datastore emulator process to terminate")
