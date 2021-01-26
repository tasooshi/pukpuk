import pukpuk


class TestConfig:

    def test_config_update_args(self):
        args = ['-n', '127.0.0.0/24', '-c', 'tests/files/pukpuk.conf']
        main = pukpuk.Main(args)
        main.init_with_args()
        del main.args.config
        del main.args.socks5_proxy
        del main.args.targets
        del main.args.hosts
        del main.args.loglevel
        del main.args.randomize
        assert main.args.__dict__ == {
            'modules': ['pukpuk.mods.response', 'pukpuk.mods.grabber'],
            'workers': 10,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
            'socket_timeout': 3.0,
            'nameserver': '192.168.100.1',
            'network': '127.0.0.0/24',
            'process_timeout': 15.0,
            'ports': ['8000', '8080', '8443/https', '9443/https'],
            'browser': 'chrome',
            'output_directory': 'pukpuk-tmp',
        }
