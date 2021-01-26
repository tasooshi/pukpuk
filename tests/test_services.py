from http import server
import pathlib
import ssl
import threading

import pukpuk


class DummyHTTPRequestHandler(server.SimpleHTTPRequestHandler):

    DUMMY_HTML = """<!DOCTYPE html>
    <html>
    <head>
        <title>Hello</title>
    </head>
    <body>
        <h3>Hello, this is {} at port {} speaking.</h3>
    </body>
    </html>"""

    def do_GET(self):
        response = self.DUMMY_HTML.format(*self.server.server_address)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def handle(self):
        try:
            super().handle()
        except ConnectionResetError:
            pass


class Services:

    def __init__(self, services):
        self.services_objs = list()
        self.threads = list()
        for srv in services:
            port = srv[0]
            proto = srv[1]
            service = server.ThreadingHTTPServer(
                ('', port),
                DummyHTTPRequestHandler,
            )
            if proto == 'https':
                service.socket = ssl.wrap_socket(service.socket, certfile='tests/files/server.pem', server_side=True)
            self.services_objs.append(service)
        for srv in self.services_objs:
            thread = threading.Thread(target=srv.serve_forever)
            thread.daemon = True
            self.threads.append(thread)

    def __enter__(self):
        [thread.start() for thread in self.threads]

    def __exit__(self, *args, **kwargs):
        [obj.shutdown() for obj in self.services_objs]


class TestServices:

    def test_http(self):
        services = (
            (8000, 'http'),
            (8080, 'http'),
        )
        with Services(services):
            args = ['-n', '127.0.0.0/29', '-c', 'tests/files/pukpuk-test.conf', '--debug']
            main = pukpuk.Main(args)
            main.init_with_args()
            main.run()
            assert set(main.targets) == {
                ('127.0.0.1', 8000, 'http'),
                ('127.0.0.1', 8080, 'http'),
            }
        assert pathlib.Path(main.args.output_directory, 'response', 'http-127.0.0.1-8000.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'response', 'http-127.0.0.1-8080.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'http-127.0.0.1-8000.png').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'http-127.0.0.1-8080.png').exists() is True
        main.delete_output()

    def test_https(self):
        services = (
            (8000, 'https'),
            (8080, 'https'),
        )
        with Services(services):
            args = ['-n', '127.0.0.0/29', '-c', 'tests/files/pukpuk-test.conf', '--debug']
            main = pukpuk.Main(args)
            main.init_with_args()
            main.run()
            assert set(main.targets) == {
                ('127.0.0.1', 8000, 'https'),
                ('127.0.0.1', 8080, 'https'),
            }
        assert pathlib.Path(main.args.output_directory, 'response', 'https-127.0.0.1-8000.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'response', 'https-127.0.0.1-8080.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'https-127.0.0.1-8000.png').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'https-127.0.0.1-8080.png').exists() is True
        main.delete_output()

    def test_mixed(self):
        services = (
            (8000, 'http'),
            (8443, 'https'),
            (8080, 'http'),
            (9443, 'https'),
        )
        with Services(services):
            args = ['-n', '127.0.0.0/29', '-c', 'tests/files/pukpuk-test.conf', '--debug']
            main = pukpuk.Main(args)
            main.init_with_args()
            main.run()
            assert set(main.targets) == {
                ('127.0.0.1', 8000, 'http'),
                ('127.0.0.1', 8080, 'http'),
                ('127.0.0.1', 8443, 'https'),
                ('127.0.0.1', 9443, 'https'),
            }
        assert pathlib.Path(main.args.output_directory, 'response', 'http-127.0.0.1-8000.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'response', 'http-127.0.0.1-8080.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'response', 'https-127.0.0.1-8443.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'response', 'https-127.0.0.1-9443.txt').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'http-127.0.0.1-8000.png').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'http-127.0.0.1-8080.png').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'https-127.0.0.1-8443.png').exists() is True
        assert pathlib.Path(main.args.output_directory, 'grabber', 'https-127.0.0.1-9443.png').exists() is True
        main.delete_output()

    def test_not_http_true(self):
        pass

    def test_prepare(self):
        pass
