import pukpuk


class TestMain:

    def test_hosts_from_cidr(self):
        args = []
        main = pukpuk.Main(args)
        output = main.hosts_from_cidr('10.0.0.0/24')
        expected = ['10.0.0.' + str(i) for i in range(256)]
        expected.pop(0)
        expected.pop(len(expected) - 1)
        assert output == expected

    def test_hosts_from_file(self):
        args = []
        main = pukpuk.Main(args)
        output = main.hosts_from_file('tests/files/hosts.txt')
        expected = [
            '192.168.100.100',
            '192.168.100.200',
        ]
        assert output == expected

    def test_targets_from_csv(self):
        args = []
        main = pukpuk.Main(args)
        main.targets_from_csv('tests/files/targets.csv')
        expected = [
            ('127.0.0.1', 80, ''),
            ('127.0.0.1', 443, 'https'),
            ('127.0.0.1', 8080, 'http'),
        ]
        assert main.targets == expected

    def test_build_url(self):
        args = []
        main = pukpuk.Main(args)
        output = main.build_url('example.com', 8080, 'https')
        expected = 'https://example.com:8080/'
        assert output == expected
