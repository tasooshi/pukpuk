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
def socks(docker_ip, docker_services):
    docker_port = docker_services.port_for('socks', 22)
    docker_services.wait_until_responsive(check=lambda: available(docker_ip, docker_port), timeout=30, pause=2)
    socks_host = '127.0.0.1'
    socks_port = '1080'
    key_file = pathlib.Path(__file__).parent / 'dockers' / 'socks' / 'test_id_rsa'
    exec_args = [
        'ssh',
        '-i',
        str(key_file),
        f'user@{docker_ip}',
        '-p',
        str(docker_port),
        '-N',
        '-D',
        socks_port,
    ]
    subprocess.Popen(exec_args)
    return f'{socks_host}:{socks_port}'


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
