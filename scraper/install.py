import logging
import platform
import enum
import os
import requests
import shutil
import subprocess
import sys
from urllib import parse


LOG = logging.getLogger('gitlawca')


class SystemPlatform(enum.Enum):
    LINUX_64 = 1
    LINUX_32 = 2
    MACOS_64 = 3
    MACOS_32 = 4
    WIN_64 = 5
    WIN_32 = 6


GCLOUD_PREFIX = 'https://dl.google.com/dl/cloudsdk/channels/rapid/downloads'
GCLOUD_VERSION = '154.0.1'

GCLOUD_DISTRIBUTIONS = {
    SystemPlatform.LINUX_64: '{}/google-cloud-sdk-{}-linux-x86_64.tar.gz'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
    SystemPlatform.LINUX_32: '{}/google-cloud-sdk-{}-linux-x86.tar.gz'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
    SystemPlatform.MACOS_64: '{}/google-cloud-sdk-{}-darwin-x86_64.tar.gz'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
    SystemPlatform.MACOS_32: '{}/google-cloud-sdk-{}-darwin-x86.tar.gz'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
    SystemPlatform.WIN_64: '{}/google-cloud-sdk-{}-windows-x86_64.zip'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
    SystemPlatform.WIN_32: '{}/google-cloud-sdk-{}-windows-x86.zip'.format(GCLOUD_PREFIX, GCLOUD_VERSION),
}


class UnsupportedSystemError(Exception):
    pass


def get_platform() -> SystemPlatform:
    if platform.system() == 'Darwin':
        is_64_bit = sys.maxsize > 2**32
        system = SystemPlatform.MACOS_64 if is_64_bit else SystemPlatform.MACOS_32
    elif platform.system() == 'Linux':
        is_64_bit = platform.architecture()[0] == '64bit'
        system = SystemPlatform.LINUX_64 if is_64_bit else SystemPlatform.LINUX_32
    elif platform.system() == 'Windows':
        is_64_bit = platform.architecture()[0] == '64bit'
        system = SystemPlatform.WIN_64 if is_64_bit else SystemPlatform.WIN_32
    else:
        raise UnsupportedSystemError()
    LOG.warning("Platform detected: {}".format(system.name))
    return system


def get_distribution_url(system: SystemPlatform) -> str:
    return GCLOUD_DISTRIBUTIONS[system]


def detect_gcloud(system: SystemPlatform) -> bool:
    LOG.warning("PATH={}".format(os.environ['PATH']))
    if system in {SystemPlatform.LINUX_64, SystemPlatform.LINUX_32, SystemPlatform.MACOS_64, SystemPlatform.MACOS_32}:
        return subprocess.run(['which', 'gcloud'], stdout=subprocess.PIPE).stdout != b''
    else:
        return subprocess.run(['where', 'gcloud'], stdout=subprocess.PIPE).stdout != b''


def gcloud_folder(root_folder: str) -> str:
    gcloud_path = os.path.join(root_folder, '.gcloud')
    if os.path.exists(gcloud_path):
        shutil.rmtree(gcloud_path)
    os.makedirs(gcloud_path)
    return gcloud_path


def download_gcloud(root_folder: str, system: SystemPlatform) -> str:
    gcloud_path = gcloud_folder(root_folder)
    url = get_distribution_url(system)
    local_filename = parse.urlparse(url).path.split('/')[-1]

    destination_file = os.path.join(gcloud_path, local_filename)

    LOG.warning("Downloading gcloud package from {} to local path {}".format(local_filename, destination_file))
    response = requests.get(url, stream=True)
    with open(destination_file, 'wb') as f:
        shutil.copyfileobj(response.raw, f)

    destination_folder = os.path.dirname(destination_file)
    shutil.unpack_archive(destination_file, extract_dir=destination_folder)
    LOG.warning("Unpacked gcloud package into {}".format(destination_folder))
    return destination_folder


def run_gcloud_installation(base_path: str) -> None:
    path = os.path.join(base_path, 'google-cloud-sdk', 'install.sh')
    LOG.warning('Installing gcloud SDK')
    subprocess.run([path, '--additional-components', 'beta', 'cloud-datastore-emulator', '--quiet'])
    LOG.warning('To add gcloud to your bash path and add autocompletion, source these files:')
    LOG.warning("- source '{}/google-cloud-sdk/path.bash.inc'".format(base_path))
    LOG.warning("- source '{}/google-cloud-sdk/completion.bash.inc'".format(base_path))
    LOG.warning('Installed gcloud SDK')


def install_gcloud(root_folder: str) -> None:
    system = get_platform()
    if not detect_gcloud(system):
        LOG.warning("gcloud installation not detected. Installing...")
        destination_folder = download_gcloud(root_folder, system)
        run_gcloud_installation(destination_folder)


def installation_folder() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


if __name__ == '__main__':
    LOG.warning("Installing gcloud to {}".format(installation_folder()))
    install_gcloud(installation_folder())
