#!/usr/bin/env python3
import threading
from http import server

import ssl


class DummyHTTPRequestHandler(server.SimpleHTTPRequestHandler):

    DUMMY_HTML = """<!DOCTYPE html>
    <html>
    <head>
        <title>Hello</title>
    </head>
    <body>
        <h3>Hello {client_host}, this is {server_host} at port {server_port} speaking.</h3>
        <h4>Your User-Agent is {user_agent}</h4>
    </body>
    </html>"""

    def do_GET(self):
        response = self.DUMMY_HTML.format(
            client_host=self.client_address[0],
            server_host=self.server.server_address[0],
            server_port=self.server.server_address[1],
            user_agent=self.headers['User-Agent']
        )
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

    PORTS = (
        (80, 'http'),
        (443, 'https'),
        (8000, 'http'),
        (8080, 'http'),
        (8443, 'https'),
        (9443, 'https'),
    )

    def __init__(self):
        self.services = list()
        self.threads = list()
        self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE
        self.ssl_ctx.load_cert_chain('/opt/server.pem')
        for srv in self.PORTS:
            port = srv[0]
            proto = srv[1]
            service = server.ThreadingHTTPServer(
                ('', port),
                DummyHTTPRequestHandler,
            )
            if proto == 'https':
                service.socket = self.ssl_ctx.wrap_socket(service.socket, server_side=True)
            self.services.append(service)
        for srv in self.services:
            thread = threading.Thread(target=srv.serve_forever)
            self.threads.append(thread)

    def run(self):
        [thread.start() for thread in self.threads]

    def stop(self):
        [obj.shutdown() for obj in self.services]

    def __enter__(self):
        self.run()

    def __exit__(self, *args, **kwargs):
        self.stop()


if __name__ == '__main__':
    Services().run()
