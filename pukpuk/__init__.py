#!/usr/bin/env python3

import argparse
import asyncio
import atexit
import concurrent.futures
import concurrent.futures.thread
from datetime import datetime
import ipaddress
import socket
import ssl
import urllib3

import dns.resolver
import dns.reversename
import dns.exception
import requests
from OpenSSL import crypto

import pukpuk
from pukpuk.core import (
    imports,
    logging,
)


__version__ = '0.3'


urllib3.disable_warnings()
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
atexit.unregister(concurrent.futures.thread._python_exit)


class Main:

    def __init__(self, args):
        self.args = args
        if self.args.cidr:
            self.ips = [str(ip) for ip in ipaddress.ip_network(self.args.cidr).hosts()]
        elif self.args.hosts:
            with open(args.hosts) as fil:
                self.ips = [line.rstrip() for line in fil]
        else:
            raise Exception('Provide --cidr or --hosts argument')

        self.ports = [arg_port.split('/') for arg_port in self.args.ports]
        self.discovered = dict()
        self.urls = list()
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers)
        self.now = datetime.now()
        self.modules = list()
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [self.args.resolver]
        self.headers = requests.utils.default_headers()
        self.headers['User-Agent'] = self.args.user_agent

    def build_url(self, host, port, proto):
        return f'{proto}://{host}:{port}/'

    def discover(self, ip, port, proto):
        logging.logger.debug(f'Trying {ip}:{port}...')
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.args.socket_timeout)
            sock.connect((ip, int(port)))
        except (OSError, TimeoutError, socket.timeout):
            pass
        else:
            self.discovered[(ip, port, proto)] = list()
            logging.logger.info(f'Discovered {ip}:{port}')
            # If HTTPS extract certificate details and add all extra host names to the list
            if proto == 'https':
                try:
                    with ssl_ctx.wrap_socket(sock, server_hostname=ip) as ssock:
                        cert = ssock.getpeercert(True)
                        x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)
                        for i in range(0, x509.get_extension_count()):
                            ext = x509.get_extension(i)
                            if 'subjectAltName' in str(ext.get_short_name()):
                                for alt in [alt.split(':')[1] for alt in str(ext).split(',')]:
                                    if not ('*' in alt or '@' in alt):
                                        try:
                                            int(alt)
                                        except ValueError:
                                            # That's right, append on exception
                                            self.discovered[(ip, port, proto)].append(alt)
                                        else:
                                            pass
                except (OSError, ConnectionResetError, socket.timeout, ssl.SSLError):
                    logging.logger.info(f'Handshake failure for {ip}:{port} - outdated SSL?')

    def generate(self, base, alts):
        # Add the host and port combination
        self.urls.append(self.build_url(*base))

        # Add URL based on resolved name for that IP address
        try:
            response = self.resolver.query(dns.reversename.from_address(base[0]), 'PTR')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            pass
        else:
            fqdn = response.rrset.items[0].to_text().rstrip('.')
            self.urls.append(self.build_url(fqdn.lower(), base[1], base[2]))

        # Now all the alternative names
        for alt in alts:
            self.urls.append(self.build_url(alt.lower(), base[1], base[2]))

    def prepare(self):
        self.urls = list(set(self.urls))

    def run_tasks(self, tasks):
        try:
            self.loop = asyncio.get_event_loop()
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers)
            future = asyncio.gather(*tasks, return_exceptions=True)
            self.loop.run_until_complete(future)
        except KeyboardInterrupt:
            logging.logger.info('Step canceled!')
            [fut.cancel() for fut in tasks]

    def run(self, parser):
        # Initialize modules and check arguments
        for module in self.args.modules:
            module = imports.class_import(module)()
            module.extra_args(parser)
            args = parser.parse_args()
            module.init(vars(args), self)
            self.modules.append(module)

        logging.logger.info('Looking for hosts...')
        futures = [
            self.loop.run_in_executor(self.executor, self.discover, ip, port, proto) for ip in self.ips for port, proto in self.ports
        ]
        self.run_tasks(futures)

        logging.logger.info('Generating URLs...')
        futures = [
            self.loop.run_in_executor(self.executor, self.generate, base, alts) for base, alts in self.discovered.items() if alts is not None
        ]
        self.run_tasks(futures)

        self.prepare()

        logging.logger.info(f'Using DNS: {self.args.resolver}')

        # Now run the modules
        for module in self.modules:
            self.run_tasks(
                [self.loop.run_in_executor(self.executor, module.execute, url) for url in self.urls]
            )


def entry_point():

    headers = requests.utils.default_headers()
    resolver = dns.resolver.Resolver(configure=True)
    resolver.nameservers = [resolver.nameservers[0]]

    parser = argparse.ArgumentParser(description='HTTP screen grabber and response dumper.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--cidr', help='CIDR notation, e.g. "10.0.0.0/24"')
    group.add_argument('-l', '--hosts', help='IP list in a text file')
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.logging.DEBUG, default=logging.logging.INFO)
    parser.add_argument('-e', '--executable', default='chromium', help='E.g. "chrome"')
    parser.add_argument('-m', '--modules', nargs='*', default=['pukpuk.mods.response'], help='Modules to be used')
    parser.add_argument('-p', '--ports', nargs='+', default=['80/http', '443/https'], help='E.g. "-p 80/http 443/https 8000/http 8443/https"')
    parser.add_argument('-pt', '--process-timeout', type=int, default=8, help='Process timeout in seconds')
    parser.add_argument('-r', '--resolver', default=resolver.nameservers[0], help='DNS server')
    parser.add_argument('-st', '--socket-timeout', type=int, default=2, help='Socket timeout in seconds')
    parser.add_argument('-ua', '--user-agent', default=headers['User-Agent'], help='Custom user agent')
    parser.add_argument('-v', '--version', action='version', version=pukpuk.__version__)
    parser.add_argument('-w', '--workers', default=16, type=int, help='Number of concurrent workers')
    args, _ = parser.parse_known_args()

    logging.init(args.loglevel)

    main = Main(args)
    main.run(parser)


if __name__ == '__main__':
    entry_point()
