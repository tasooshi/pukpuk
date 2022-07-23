from pukpuk import base


def test_get_discovery_targets(http, tmp_dir):
    target_ip, _ = http
    app = base.Application(output_dir=tmp_dir)
    targets = (
        (target_ip, 8000, 'http'),
        (target_ip, None, 'http'),
        (target_ip, 8888, None),
        (target_ip, 80, 'http'),
    )
    services = (
        (8080, 'http'),
        (8443, 'https'),
    )
    assert set(app.get_discovery_targets(targets, services)) == {
        (target_ip, 80, 'http'),
        (target_ip, 8000, 'http'),
        (target_ip, 8080, 'http'),
        (target_ip, 8443, 'https'),
        ('localhost', 80, 'http'),
        ('localhost', 8000, 'http'),
        ('localhost', 8080, 'http'),
        ('localhost', 8443, 'https'),
    }


def test_get_discovery_targets_different(http, tmp_dir):
    target_ip, _ = http
    app = base.Application(output_dir=tmp_dir)
    targets = (
        (target_ip, 8000, 'http'),
        (target_ip, None, 'http'),
        (target_ip, 8888, None),
        (target_ip, 80, 'http'),
    )
    services = (
        (443, 'https'),
        (8080, 'http'),
        (8443, 'https'),
        (9443, 'https'),
    )
    assert set(app.get_discovery_targets(targets, services)) == {
        (target_ip, 80, 'http'),
        (target_ip, 443, 'https'),
        (target_ip, 8000, 'http'),
        (target_ip, 8080, 'http'),
        (target_ip, 8443, 'https'),
        (target_ip, 9443, 'https'),
        ('localhost', 8000, 'http'),
        ('localhost', 443, 'https'),
        ('localhost', 80, 'http'),
        ('localhost', 8080, 'http'),
        ('localhost', 8443, 'https'),
        ('localhost', 9443, 'https'),
    }
