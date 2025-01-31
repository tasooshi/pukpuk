from pukpuk import base


def test_get_discovery_targets(tmp_dir):
    app = base.Application(output_dir=tmp_dir)
    targets = (
        ('127.0.0.1', 8000, 'http'),
        ('127.0.0.1', None, 'http'),
        ('127.0.0.1', 8888, None),
        ('127.0.0.1', 80, 'http'),
    )
    services = (
        (8080, 'http'),
        (8443, 'https'),
    )
    assert set(app.get_discovery_targets(targets, services)) == {
        ('127.0.0.1', 80, 'http'),
        ('127.0.0.1', 8000, 'http'),
        ('127.0.0.1', 8080, 'http'),
        ('127.0.0.1', 8443, 'https'),
        ('localhost', 80, 'http'),
        ('localhost', 8000, 'http'),
        ('localhost', 8080, 'http'),
        ('localhost', 8443, 'https'),
    }


def test_get_discovery_targets_different(tmp_dir):
    app = base.Application(output_dir=tmp_dir)
    targets = (
        ('127.0.0.1', 8000, 'http'),
        ('127.0.0.1', None, 'http'),
        ('127.0.0.1', 8888, None),
        ('127.0.0.1', 80, 'http'),
    )
    services = (
        (443, 'https'),
        (8080, 'http'),
        (8443, 'https'),
        (9443, 'https'),
    )
    assert set(app.get_discovery_targets(targets, services)) == {
        ('127.0.0.1', 80, 'http'),
        ('127.0.0.1', 443, 'https'),
        ('127.0.0.1', 8000, 'http'),
        ('127.0.0.1', 8080, 'http'),
        ('127.0.0.1', 8443, 'https'),
        ('127.0.0.1', 9443, 'https'),
        ('localhost', 8000, 'http'),
        ('localhost', 443, 'https'),
        ('localhost', 80, 'http'),
        ('localhost', 8080, 'http'),
        ('localhost', 8443, 'https'),
        ('localhost', 9443, 'https'),
    }
