import pathlib
import shlex

import pytest

from pukpuk import (
    base,
)


def test_socks_proxy(http, tmp_dir, socks):
    target_ip, _ = http
    args = shlex.split(f'-N 192.168.2.2/32 -x {socks} -p 80/http,8000/http -o {tmp_dir}')
    app = base.Application()
    app.parse(args)
    assert pathlib.Path(tmp_dir, 'response', 'http-192.168.2.2-80.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'response', 'http-192.168.2.2-8000.txt').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-192.168.2.2-80.png').exists() is True
    assert pathlib.Path(tmp_dir, 'screens', 'http-192.168.2.2-8000.png').exists() is True
    contents = pathlib.Path(tmp_dir, 'response', 'http-192.168.2.2-8000.txt').read_text()
    assert 'Hello 192.168.2.3' in contents
