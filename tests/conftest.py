import pathlib
import shutil
import socket
import subprocess
import tempfile

import pytest


def available(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip, port))
    except socket.error:
        return False
    else:
        return True


@pytest.fixture(scope='session')
def http(docker_ip, docker_services):
    docker_port = docker_services.port_for('http', 80)
    docker_services.wait_until_responsive(check=lambda: available(docker_ip, docker_port), timeout=30, pause=1)
    return docker_ip, docker_port


@pytest.fixture
def cwd():
    return pathlib.Path(__file__).parent


@pytest.fixture(scope='function')
def tmp_dir():
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
