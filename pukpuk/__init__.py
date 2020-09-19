#!/usr/bin/env python3

import csv
from datetime import datetime
import argparse
import asyncio
import atexit
import concurrent.futures
import concurrent.futures.thread
import ipaddress
import pathlib
import socket
import ssl
import urllib3

from OpenSSL import crypto
import dns.exception
import dns.resolver
import dns.reversename
import requests

import pukpuk
from pukpuk.core import (
    imports,
    logging,
)


__version__ = '0.5'


urllib3.disable_warnings()
ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
atexit.unregister(concurrent.futures.thread._python_exit)


OUTPUT_DIR_EXT = '.pukpuk'


class Main:

    DEFAULT_MODULES = [
        'pukpuk.mods.response',
        'pukpuk.mods.grabber',
    ]

    def __init__(self, args):
        self.args = args
        if self.args.discovery_cidr:
            self.ips = [str(ip) for ip in ipaddress.ip_network(self.args.discovery_cidr).hosts()]
        elif self.args.discovery_list:
            with open(args.discovery_list) as fil:
                self.ips = [line.rstrip() for line in fil]
        elif not self.args.input_list:
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
                    ssock = ssl_ctx.wrap_socket(sock, server_hostname=ip)
                    cert = ssock.getpeercert(True)
                except (OSError, ConnectionResetError, socket.timeout, ssl.SSLError):
                    logging.logger.debug(f'SSL handshake failed for {ip}:{port}')
                else:
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
        for module_path in self.DEFAULT_MODULES:
            module = imports.class_import(module_path)()
            module.extra_args(parser)
            args = parser.parse_args()
            module.init(vars(args), self)
            self.modules.append(module)

        if self.args.input_list:
            # Skip discovery, read from CSV file
            with open(args.input_list, newline='') as fil:
                list_reader = csv.reader(fil)
                for row in list_reader:
                    # Assiging boolean here is both a bit ugly and inefficient, keeps interface consistent though
                    self.discovered[row[0], row[1], row[2]] = True
        else:
            # Host discovery
            logging.logger.info('Looking for hosts...')
            futures = [
                self.loop.run_in_executor(self.executor, self.discover, ip, port, proto) for ip in self.ips for port, proto in self.ports
            ]
            self.run_tasks(futures)

        # Generate list of URLs to be used with modules
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


def get_dir():
    name_date = datetime.now().strftime('%Y%m%d_%H%M')
    name = name_date + OUTPUT_DIR_EXT
    suffix = 0
    while pathlib.Path(name).exists():
        suffix += 1
        name = name_date + '-' + str(suffix) + OUTPUT_DIR_EXT
    return name


def entry_point():

    def show_default(value):
        display = ', '.join(value) if isinstance(value, list) else value
        return f' (default: {display})'

    headers = requests.utils.default_headers()
    resolver = dns.resolver.Resolver(configure=True)
    resolver.nameservers = [resolver.nameservers[0]]

    ARGUMENT_DEFAULTS = {
        'workers': 6,
        'user_agent': headers['User-Agent'],
        'socket_timeout': 3,
        'resolver': resolver.nameservers[0],
        'process_timeout': 10,
        'ports': ['80/http', '443/https'],
        'executable': 'chromium',
        'output_directory': get_dir(),
    }

    parser = argparse.ArgumentParser(
        description='HTTP screen grabber and response dumper',
        epilog=(
            'Examples:\n\n'
            '\t$ pukpuk -c 10.1.1.0/24\n\n'
            '\t$ pukpuk -i hosts-ports.csv\n\n'
            '\t$ pukpuk -l hosts.txt -e /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome -ua "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15" -p 80/http 81/http 82/http 443/https 4443/https 1080/http 1443/https 8000/http 8001/http 8008/http 8080/http 8081/http 8088/http 8888/http 9000/http 9080/http 7443/https 8443/https 9443/https 10443/https 11443/https 12443/https\n\n'
            '---'
            '\n\n'
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.print_usage = parser.print_help

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--discovery-cidr', help='Discovery mode, accepts CIDR notation, e.g. "10.0.0.0/24"')
    group.add_argument('-l', '--discovery-list', help='Discovery mode, accepts file input, one IP address per line')
    group.add_argument('-i', '--input-list', help='Skips discovery, accepts file input, CSV format: [address],[port],[protocol], e.g. "192.168.1.1,443,https"')
    parser.add_argument('-o', '--output-directory', default=ARGUMENT_DEFAULTS['output_directory'], help='Path where results (text files, images) will be stored' + show_default(ARGUMENT_DEFAULTS['output_directory']))
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.logging.DEBUG, default=logging.logging.INFO)
    parser.add_argument('-e', '--executable', default=ARGUMENT_DEFAULTS['executable'], help='Browser binary path for headless screen grabbing' + show_default(ARGUMENT_DEFAULTS['executable']))
    parser.add_argument('-p', '--ports', nargs='+', default=ARGUMENT_DEFAULTS['ports'], help='Port list for HTTP service discovery' + show_default(ARGUMENT_DEFAULTS['ports']))
    parser.add_argument('-pt', '--process-timeout', type=int, default=ARGUMENT_DEFAULTS['process_timeout'], help='Process timeout in seconds' + show_default(ARGUMENT_DEFAULTS['process_timeout']))
    parser.add_argument('-r', '--resolver', default=ARGUMENT_DEFAULTS['resolver'], help='DNS server' + show_default(ARGUMENT_DEFAULTS['resolver']))
    parser.add_argument('-st', '--socket-timeout', type=int, default=ARGUMENT_DEFAULTS['socket_timeout'], help='Socket timeout in seconds' + show_default(ARGUMENT_DEFAULTS['socket_timeout']))
    parser.add_argument('-ua', '--user-agent', default=ARGUMENT_DEFAULTS['user_agent'], help='Browser User-Agent header' + show_default(ARGUMENT_DEFAULTS['user_agent']))
    parser.add_argument('-v', '--version', action='version', version=pukpuk.__version__)
    parser.add_argument('-w', '--workers', default=ARGUMENT_DEFAULTS['workers'], type=int, help='Number of concurrent workers' + show_default(ARGUMENT_DEFAULTS['workers']))
    args, _ = parser.parse_known_args()

    # Create output directory
    pathlib.Path(args.output_directory).mkdir(parents=True, exist_ok=True)

    # Initiate logging
    logging.init(args.loglevel, args.output_directory)

    main = Main(args)
    main.run(parser)

    logging.logger.info(f'Results in: {args.output_directory}')


if __name__ == '__main__':
    entry_point()
