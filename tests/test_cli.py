import pathlib
import shlex

import pytest

from pukpuk import (
    base,
    version,
)


def test_version(capsys):
    args = shlex.split('-v')
    app = base.Application()
    with pytest.raises(SystemExit) as exc:
        app.parse(args)
    assert exc.type == SystemExit
    assert exc.value.code == 0
    out, err = capsys.readouterr()
    assert version.__version__ == out.strip()


def test_cidr(http, tmp_dir):
    target_ip, _ = http
    args = shlex.split(f'-N 127.0.0.1/32 -p 80/http,8000/http,8080/http,8443/https -o {tmp_dir}')
    app = base.Application()
    app.parse(args)
    assert pathlib.Path(tmp_dir, 'response', 'http-127.0.0.1-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-127.0.0.1-8080.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'https-127.0.0.1-8443.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-localhost-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-localhost-8080.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'https-localhost-8443.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-127.0.0.1-8000.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-127.0.0.1-8080.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'https-127.0.0.1-8443.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-localhost-8000.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-localhost-8080.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'https-localhost-8443.png').exists() is True


def test_file(http, tmp_dir, cwd):
    target_ip, _ = http
    args = shlex.split(f'-T {cwd}/files/hosts.txt -o {tmp_dir}')
    app = base.Application()
    app.parse(args)
    assert pathlib.Path(tmp_dir, 'response', 'http-127.0.0.1-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'https-127.0.0.1-9443.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-localhost-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'https-localhost-9443.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-127.0.0.1-8000.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'https-127.0.0.1-9443.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-localhost-8000.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'https-localhost-9443.png').exists() is True


def test_user_agent_and_ports(http, tmp_dir):
    target_ip, _ = http
    args = shlex.split(f'-N 127.0.0.1/32 -p 80/http,8000/http -o {tmp_dir} -u "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0"')
    app = base.Application()
    app.parse(args)
    assert pathlib.Path(tmp_dir, 'response', 'http-127.0.0.1-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-localhost-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-127.0.0.1-8000.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-localhost-8000.png').exists() is True
    contents = pathlib.Path(tmp_dir, 'response', 'http-localhost-8000.txt').read_text()
    assert 'Mozilla/5.0' in contents
