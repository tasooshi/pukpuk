import pathlib
import shutil
import socket
import tempfile

import pytest


@pytest.fixture
def cwd():
    return pathlib.Path(__file__).parent


@pytest.fixture(scope='function')
def tmp_dir():
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
