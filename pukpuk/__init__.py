#!/usr/bin/env python3

from datetime import datetime
import argparse
import asyncio
import atexit
import concurrent.futures
import concurrent.futures.thread
import configparser
import csv
import ipaddress
import os
import pathlib
import random
import shutil
import socket
import socks
import ssl
import sys
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


__version__ = '2.0.4'


urllib3.disable_warnings()
ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
atexit.unregister(concurrent.futures.thread._python_exit)


default_resolver = dns.resolver.Resolver(configure=True)


OUTPUT_DIR_EXT = '.pukpuk'


def get_output_dir():
    name_date = datetime.now().strftime('%Y%m%d_%H%M')
    name = name_date + OUTPUT_DIR_EXT
    suffix = 0
    while pathlib.Path(name).exists():
        suffix += 1
        name = name_date + '-' + str(suffix) + OUTPUT_DIR_EXT
    return name


class Main:

    PROTO_HTTP = 'http'
    PROTO_HTTPS = 'https'
    PROTO_UNKNOWN = None

    def __init__(self, orig_args):
        self.orig_args = orig_args
        self.args = None
        self.parser = None
        self.proxy = None
        self.executor = None
        self.resolver = None
        self.targets = list()
        self.urls = list()
        self.modules = list()
        self.headers = requests.utils.default_headers()
        self.defaults = {
            'modules': [
                'pukpuk.mods.response',
                'pukpuk.mods.grabber',
            ],
            'workers': 6,
            'user_agent': self.headers['User-Agent'],
            'socket_timeout': 2.5,
            'nameserver': default_resolver.nameservers[0],
            'process_timeout': 12.5,
            'ports': ['80/http', '8000/http', '8080/http', '443/https', '8443/https'],
            'browser': 'chromium',
            'config': os.path.join(os.getcwd(), 'pukpuk.conf'),
            'output_directory': get_output_dir(),
        }

    def config_to_dict(self, path):
        config = configparser.ConfigParser()
        config.read(path)
        config_dict = dict(config[config.default_section].items())
        if 'ports' in config_dict:
            config_dict['ports'] = config_dict['ports'].split(',')
        if 'modules' in config_dict:
            config_dict['modules'] = config_dict['modules'].split(',')
        if 'workers' in config_dict:
            config_dict['workers'] = int(config_dict['workers'])
        if 'socket_timeout' in config_dict:
            config_dict['socket_timeout'] = float(config_dict['socket_timeout'])
        if 'process_timeout' in config_dict:
            config_dict['process_timeout'] = float(config_dict['process_timeout'])
        return config_dict

    def init_with_args(self):
        self.parser = argparse.ArgumentParser(
            description='HTTP discovery and change monitoring tool',
            epilog=(
                'Examples:\n\n'
                '\t$ pukpuk -n 10.1.1.0/24\n\n'
                '\t$ pukpuk -t targets.csv\n\n'
                '\t$ pukpuk -l hosts.txt -b /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome -u "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15" -p 80/http 81 82 443/https 4443/https 1080 1443/https 8000 8001 8008 8080 8081 8088 8888 9000 9080 7443/https 8443/https 9443/https\n\n'
                '---'
                '\n\n'
            ),
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.parser.print_usage = self.parser.print_help
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-n', '--network', help='Discovery mode, accepts network in CIDR notation, e.g. "10.0.0.0/24"')
        group.add_argument('-l', '--hosts', help='Discovery mode, accepts hosts list as a file, one IP address per line')
        group.add_argument('-t', '--targets', help='Skips discovery, accepts targets as a file, CSV format: [address],[port],[?protocol], e.g. "192.168.1.1,443,https" or "192.168.1.1,443,"')
        self.parser.add_argument('-c', '--config', default=self.defaults['config'], help='Configuration file path, overrides command line arguments and defaults' + self.show_default(self.defaults['config']))
        self.parser.add_argument('-o', '--output-directory', default=self.defaults['output_directory'], help='Path where results (text files, images) will be stored' + self.show_default(self.defaults['output_directory']))
        self.parser.add_argument('-b', '--browser', default=self.defaults['browser'], help='Browser binary path for headless screen grabbing' + self.show_default(self.defaults['browser']))
        self.parser.add_argument('-p', '--ports', nargs='+', default=self.defaults['ports'], help='Port list for HTTP service discovery' + self.show_default(self.defaults['ports']))
        self.parser.add_argument('-m', '--modules', nargs='+', default=self.defaults['modules'], help='List of modules to be executed' + self.show_default(self.defaults['modules']))
        self.parser.add_argument('-d', '--nameserver', default=self.defaults['nameserver'], help='DNS server' + self.show_default(self.defaults['nameserver']))
        self.parser.add_argument('-x', '--socks5-proxy', help='Socks5 proxy, e.g. "127.0.0.1:1080')
        self.parser.add_argument('-u', '--user-agent', default=self.defaults['user_agent'], help='Browser User-Agent header' + self.show_default(self.defaults['user_agent']))
        self.parser.add_argument('-v', '--version', action='version', version=pukpuk.__version__)
        self.parser.add_argument('-w', '--workers', default=self.defaults['workers'], type=int, help='Number of concurrent workers' + self.show_default(self.defaults['workers']))
        self.parser.add_argument('-r', '--randomize', action='store_true', help='Randomize scanning order')
        self.parser.add_argument('--process-timeout', type=float, default=self.defaults['process_timeout'], help='Process timeout in seconds' + self.show_default(self.defaults['process_timeout']))
        self.parser.add_argument('--socket-timeout', type=float, default=self.defaults['socket_timeout'], help='Socket timeout in seconds' + self.show_default(self.defaults['socket_timeout']))
        self.parser.add_argument('--debug', action='store_const', dest='loglevel', const=logging.logging.DEBUG, default=logging.logging.INFO)
        self.args, _ = self.parser.parse_known_args(self.orig_args)
        self.args.__dict__.update(self.config_to_dict(self.args.config))
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers)
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = self.args.socket_timeout
        self.resolver.nameservers = [self.args.nameserver]
        self.headers['User-Agent'] = self.args.user_agent
        if self.args.socks5_proxy:
            try:
                self.proxy = self.args.socks5_proxy.split(':')
            except Exception as exc:
                raise exc
        logging.logger.info('Using DNS: {}'.format(', '.join(self.resolver.nameservers)))

    def show_default(self, value):
        """Render help text default value"""

        display = ', '.join(value) if isinstance(value, list) else value
        return f' (default: {display})'

    def hosts_from_cidr(self, cidr):
        """Converts CIDR string to list of IP addresses"""

        return [str(ip) for ip in ipaddress.ip_network(cidr).hosts()]

    def hosts_from_file(self, path):
        """Loads list of IP addresses from a flat text file"""

        with open(path) as fil:
            return [line.rstrip() for line in fil]

    def targets_from_csv(self, path):
        """Loads list of targets (host, port and protocol) from a CSV file"""

        try:
            with open(path, newline='') as fil:
                list_reader = csv.reader(fil)
                for row in list_reader:
                    self.targets.append((row[0], int(row[1]), row[2].rstrip()))
        except IndexError:
            logging.logger.info('Invalid CSV input')
            exit(1)

    def cleanup_targets(self):
        """Make list of targets unique"""

        self.targets = list(set(self.targets))

    def cleanup_urls(self):
        """Make list of URLs unique"""

        self.urls = list(set(self.urls))

    def build_url(self, host, port, proto):
        """Converts (host, port, protocol) tuple to URL"""

        return f'{proto}://{host}:{port}/'

    def port_test(self, host, port):
        """Check if given service is HTTP(S), returns None otherwise"""

        logging.logger.debug(f'Checking protocol for {host}:{port}...')
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.args.socket_timeout)
        sock.connect((host, int(port)))
        request = 'HEAD / HTTP/1.0\r\nHost: {}\r\nAccept: text/html\r\n\r\n'.format(host)
        sock.sendall(request.encode('ascii'))

        check_https = False
        try:
            response = sock.recv(4096)
        except ConnectionResetError:
            check_https = True
        else:
            if response:
                if b'400' in response and b'Bad Request' in response:
                    check_https = True
            else:
                check_https = True
        sock.close()

        if check_https:
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.args.socket_timeout)
            sock.connect((host, int(port)))
            try:
                ssock = ssl_ctx.wrap_socket(sock, server_hostname=host)
                ssock.getpeercert(True)
            except (ConnectionResetError, socket.timeout, ssl.SSLError):
                logging.logger.debug(f'SSL handshake failed for {host}:{port}')
            else:
                logging.logger.debug(f'{host}:{port} seems to be HTTPS')
                return self.PROTO_HTTPS
            finally:
                sock.close()
        else:
            if b'HTTP' in response:
                logging.logger.debug(f'{host}:{port} seems to be HTTP')
                return self.PROTO_HTTP
            else:
                logging.logger.debug(f'{host}:{port} doesn\'t seem to be HTTP at all')

        return self.PROTO_UNKNOWN

    def discover(self, host, port, proto):
        """Adds successfully connected ports to targets, parse HTTPS certificate if applicable"""

        logging.logger.debug(f'Trying {host}:{port}...')

        if not proto:
            proto = self.port_test(host, port)

        if proto is self.PROTO_UNKNOWN:
            return

        with socks.socksocket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if self.proxy:
                sock.set_proxy(socks.SOCKS5, self.proxy[0], int(self.proxy[1]))
            sock.settimeout(self.args.socket_timeout)
            try:
                sock.connect((host, int(port)))
            except (OSError, TimeoutError, socket.timeout):
                pass
            else:
                self.targets.append((host, port, proto))
                logging.logger.info(f'Discovered {host}:{port}')

            # If HTTPS extract certificate details and add all extra host names to the list
            if proto == self.PROTO_HTTPS:
                try:
                    ssock = ssl_ctx.wrap_socket(sock, server_hostname=host)
                    cert = ssock.getpeercert(True)
                except (OSError, ConnectionResetError, socket.timeout, ssl.SSLError):
                    logging.logger.debug(f'SSL handshake failed for {host}:{port}')
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
                                        self.targets.append((alt.lower(), port, proto))

    def generate(self, host, port, proto):
        """Generates list of URLs based on loaded or discovered targets"""

        if not proto:
            proto = self.port_test(host, port)

        if proto:
            # Add the host and port combination
            self.urls.append(self.build_url(host, port, proto))

            # Add URL based on resolved name for an IP address
            try:
                ipaddress.ip_address(host)
            except ValueError:
                return
            else:
                try:
                    logging.logger.debug(f'Performing reverse lookup for {host}...')
                    response = self.resolver.query(dns.reversename.from_address(host), 'PTR')
                except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.NoAnswer, dns.exception.Timeout):
                    pass
                else:
                    try:
                        fqdn = list(response.rrset.items.keys())[0].to_text().rstrip('.')
                    except KeyError:
                        pass
                    else:
                        logging.logger.debug('Added {} using reverse lookup of {}'.format(fqdn.lower(), host))
                        self.urls.append(self.build_url(fqdn.lower(), port, proto))

    def run_tasks(self, tasks):
        """Asynchronous execution method"""

        try:
            loop = asyncio.get_event_loop()
            future = asyncio.gather(*tasks, return_exceptions=True)
            loop.run_until_complete(future)
        except KeyboardInterrupt:
            logging.logger.info('Step canceled!')
            [fut.cancel() for fut in tasks]

    def delete_output(self):
        shutil.rmtree(self.args.output_directory)

    def prepare(self):
        """Main execution method"""

        loop = asyncio.get_event_loop()
        logging.logger.info('Using the following settings:')
        for key, value in self.args.__dict__.items():
            value = ', '.join(value) if isinstance(value, list) else value
            logging.logger.info(f'\t{key} = {value}')

        # Initialize modules and check arguments
        for module_path in self.args.modules:
            module = imports.class_import(module_path)()
            module.init(self)
            self.modules.append(module)

        target_args = [bool(self.args.network), bool(self.args.hosts), bool(self.args.targets)]
        if sum(target_args) > 1:
            logging.logger.info('Only one of the following arguments is allowed: --network, --hosts or --targets')
            exit(1)

        hosts = None
        if self.args.network:
            hosts = self.hosts_from_cidr(self.args.network)
        elif self.args.hosts:
            hosts = self.hosts_from_file(self.args.hosts)
        elif self.args.targets:
            self.targets_from_csv(self.args.targets)
        else:
            logging.logger.info('Provide --network, --hosts or --targets argument')
            exit(1)

        # Create output directory
        pathlib.Path(self.args.output_directory).mkdir(parents=True, exist_ok=True)

        # Initiate logging
        logging.init(self.args.loglevel, self.args.output_directory)

        # Host discovery
        if not self.targets:

            services = list()
            for arg_port in self.args.ports:
                port, _, proto = arg_port.partition('/')
                services += [(port, proto)]

            if self.args.randomize:
                random.shuffle(hosts)
                random.shuffle(services)

            logging.logger.info('Discovering...')
            futures = [
                loop.run_in_executor(self.executor, self.discover, host, int(port), proto) for host in hosts for port, proto in services
            ]
            self.run_tasks(futures)

        self.cleanup_targets()

        if self.args.randomize:
            random.shuffle(self.targets)

        # Generate list of URLs to be used with modules
        logging.logger.info('Generating URLs...')
        futures = [
            loop.run_in_executor(self.executor, self.generate, host, port, proto) for host, port, proto in self.targets
        ]
        self.run_tasks(futures)

        self.cleanup_urls()

        logging.logger.debug('URLs to be processed: {}'.format(', '.join(self.urls)))

    def run_modules(self):
        """Runs all registered modules"""
        
        loop = asyncio.get_event_loop()
        for module in self.modules:
            self.run_tasks(
                [loop.run_in_executor(self.executor, module.execute, url) for url in self.urls]
            )
        logging.logger.info(f'Results saved in: {self.args.output_directory}')

    def run(self):
        """Main execution method"""

        self.prepare()
        self.run_modules()


def entry_point():
    main = Main(sys.argv[1:])
    main.init_with_args()
    main.run()


if __name__ == '__main__':
    entry_point()
