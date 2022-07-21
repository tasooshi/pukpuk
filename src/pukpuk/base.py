import argparse
import atexit
import concurrent.futures
import concurrent.futures.thread
import ipaddress
import pathlib
import random
import socket
import ssl
import threading
from datetime import datetime
from urllib import parse

import dns.exception
import dns.resolver
import dns.reversename
import requests
import socks
import urllib3
from OpenSSL import crypto

from pukpuk import (
    logs,
    mods,
    version,
)


class Results:

    def __init__(self):
        self._items = list()
        self._lock = threading.Lock()

    def add(self, item):
        with self._lock:
            self._items.append(item)

    def get(self):
        with self._lock:
            return self._items

    def unique(self):
        with self._lock:
            return list(set(self._items))


class Application:

    PROTO_HTTP = 'http'
    PROTO_HTTPS = 'https'
    PROTO_UNKNOWN = None
    PROTO_PORTS = {
        PROTO_HTTP: 80,
        PROTO_HTTPS: 443,
    }
    OUTPUT_DIR_EXT = '.pukpuk'
    DEFAULT_BROWSER = 'chromium'
    DEFAULT_PORTS = ('80/http', '443/https')
    DEFAULT_WORKERS = 25
    DEFAULT_PROCESS_TIMEOUT = 12
    DEFAULT_SOCKET_TIMEOUT = 3

    def __init__(
        self,
        ports=None,
        browser=None,
        nameserver=None,
        randomize=False,
        socks_proxy=None,
        user_agent=None,
        workers=None,
        output_dir=None,
        process_timeout=None,
        socket_timeout=None
    ):
        self.patch()
        if nameserver is None:
            default_resolver = dns.resolver.Resolver(configure=True)
            self.nameserver = default_resolver
            self.nameserver.nameservers = default_resolver.nameservers
        else:
            self.nameserver = dns.resolver.Resolver()
            self.nameserver.nameservers = [self.nameserver]
        self.browser = self.DEFAULT_BROWSER if browser is None else browser
        self.randomize = randomize
        self.ports = list(self.DEFAULT_PORTS) if ports is None else ports
        self.process_timeout = self.DEFAULT_PROCESS_TIMEOUT if process_timeout is None else process_timeout
        self.socket_timeout = self.DEFAULT_SOCKET_TIMEOUT if socket_timeout is None else socket_timeout
        self.nameserver.timeout = self.socket_timeout
        self.socks_proxy = socks_proxy
        self.workers = self.DEFAULT_WORKERS if workers is None else workers
        self.headers = requests.utils.default_headers()
        self.user_agent = self.headers['User-Agent'] if user_agent is None else user_agent
        self.output_dir = self.get_output_dir() if output_dir is None else output_dir
        self.discovered = Results()
        self.urls = Results()
        self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def get_parser(self):
        parser = argparse.ArgumentParser(
            prog='pukpuk',
            description='HTTP discovery and change monitoring tool',
            epilog=(
                'Examples:\n\n'
                '\t$ pukpuk -T hosts.txt\n\n'
                '\t$ pukpuk -N 192.168.1.0/24 -p 80/http,81/http,82/http,8080/http,8000/http,8888/http,443/https,8443/https,4443/https\n\n'
                '---'
                '\n\n'
            ),
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.print_usage = parser.print_help
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-N', '--network', help='Discovery mode, accepts network in CIDR notation, e.g. "10.0.0.0/24"')
        group.add_argument('-T', '--targets', help='Skip discovery, load URLs from a file')
        parser.add_argument('-p', '--ports', default=','.join(self.ports), help='Port list for HTTP service discovery [Default: ' + ', '.join(self.ports) + ']')
        parser.add_argument('-b', '--browser', default=self.browser, help='Chromium browser path for headless screen grabbing [Default: ' + self.browser + ']')
        parser.add_argument('-n', '--nameserver', default=self.nameserver.nameservers[0], help='DNS server [Default: ' + self.nameserver.nameservers[0] + ']')
        parser.add_argument('-r', '--randomize', action='store_true', default=self.randomize, help='Randomize scanning order')
        parser.add_argument('-o', '--output-dir', default=self.output_dir, help='Path where results (text files, images) will be stored [Default: ' + self.output_dir + ']')
        parser.add_argument('-x', '--socks-proxy', help='Socks5 proxy, e.g. "127.0.0.1:1080"')
        parser.add_argument('-u', '--user-agent', default=self.user_agent, help='Browser User-Agent header [Default: ' + self.user_agent + ']')
        parser.add_argument('-w', '--workers', default=self.workers, type=int, help='Number of concurrent workers [Default: ' + str(self.workers) + ']')
        parser.add_argument('--process-timeout', type=float, default=self.process_timeout, help='Process timeout in seconds [Default: ' + str(self.process_timeout) + ']')
        parser.add_argument('--socket-timeout', type=float, default=self.socket_timeout, help='Socket timeout in seconds [Default: ' + str(self.socket_timeout) + ']')
        parser.add_argument('-v', '--version', action='version', version=version.__version__, help='Print version')
        verbosity = parser.add_mutually_exclusive_group()
        verbosity.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logs.logging.DEBUG, default=logs.logging.INFO)
        verbosity.add_argument('-q', '--quiet', action='store_const', dest='loglevel', const=logs.logging.NOTSET, default=logs.logging.INFO)
        return parser

    def patch(self):
        logs.logger.debug(f'Patching')
        urllib3.disable_warnings()
        atexit.unregister(concurrent.futures.thread._python_exit)

    def targets_from_cidr(self, cidr):
        """Converts CIDR string to list of IP addresses

        """
        logs.logger.debug(f'From CIDR {cidr}')
        return [(str(ip), None, None) for ip in ipaddress.ip_network(cidr).hosts()]

    def targets_from_file(self, path):
        """Loads list of IP addresses, host names and URLs from a text file

        """
        logs.logger.debug(f'From file {path}')
        with open(path) as fil:
            return [(parsed.hostname, parsed.port, parsed.scheme) for line in fil if (parsed := parse.urlsplit(line))]

    def get_url(self, host, port, proto):
        """Converts (host, port, protocol) tuple to URL

        """
        return f'{proto}://{host}:{port}/'

    def get_output_dir(self):
        name_date = datetime.now().strftime('%Y%m%d_%H%M')
        name = name_date + self.OUTPUT_DIR_EXT
        suffix = 0
        while pathlib.Path(name).exists():
            suffix += 1
            name = name_date + '-' + str(suffix) + self.OUTPUT_DIR_EXT
        logs.logger.debug(f'Output directory {name}')
        return name

    def sock_connect(self, host, port):
        logs.logger.debug(f'Connecting to {host}:{port}')
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.socket_timeout)
        if self.socks_proxy:
            sock.set_proxy(socks.SOCKS5, self.socks_proxy[0], self.socks_proxy[1])
        try:
            sock.connect((host, port))
        except socks.ProxyConnectionError:
            logs.logger.debug(f'Error when connecting to {host}:{port} through SOCKS proxy: {self.socks_proxy}')
        except Exception as exc:
            logs.logger.debug(f'Error when connecting to {host}:{port}: {exc}')
        if self.socks_proxy or sock:
            return sock

    def port_test(self, host, port):
        """Check if given service is HTTP(S), returns None otherwise

        """
        sock = self.sock_connect(host, port)
        request = 'HEAD / HTTP/1.0\r\nHost: {}\r\nAccept: text/html\r\n\r\n'.format(host)
        sock.sendall(request.encode('ascii'))

        check_https = False
        try:
            response = sock.recv(4096)
        except ConnectionResetError:
            check_https = True
            response = ''
        else:
            if response:
                if b'400' in response and b'Bad Request' in response:
                    check_https = True
            else:
                check_https = True
        sock.close()

        if check_https:
            logs.logger.debug(f'Checking if {host}:{port} is encrypted')
            sock = self.sock_connect(host, port)
            try:
                ssock = self.ssl_ctx.wrap_socket(sock, server_hostname=host)
                ssock.getpeercert(True)
            except (ConnectionResetError, socket.timeout, ssl.SSLError):
                logs.logger.debug(f'Probably not encrypted {host}:{port}')
            else:
                return self.PROTO_HTTPS
            sock.close()
        else:
            if b'HTTP' in response:
                return self.PROTO_HTTP
        return self.PROTO_UNKNOWN

    def discover(self, target):
        """Adds successfully connected ports to targets, parse HTTPS certificate if applicable

        """
        logs.logger.debug(f'Discovering {target}')
        host, port, proto = target
        if not proto:
            proto = self.port_test(host, port)

        if proto is self.PROTO_UNKNOWN:
            return

        sock = self.sock_connect(host, port)
        if sock:
            self.discovered.add((host, port, proto))
            logs.logger.info(f'Added {proto}://{host}:{port} to discoveries')
            # NOTE: If HTTPS extract certificate details and add all extra host names to the list
            if proto == self.PROTO_HTTPS:
                try:
                    ssock = self.ssl_ctx.wrap_socket(sock, server_hostname=host)
                    cert = ssock.getpeercert(True)
                except (OSError, ConnectionResetError, socket.timeout, ssl.SSLError):
                    logs.logger.debug(f'Probably not encrypted {host}:{port}')
                else:
                    logs.logger.debug(f'Parsing certificate for {host}:{port}')
                    x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)
                    for i in range(0, x509.get_extension_count()):
                        ext = x509.get_extension(i)
                        if 'subjectAltName' in str(ext.get_short_name()):
                            for alt in [alt.split(':')[1] for alt in str(ext).split(',')]:
                                if not ('*' in alt or '@' in alt):
                                    try:
                                        int(alt)
                                    except ValueError:
                                        cert_host = alt.lower()
                                        self.discovered.add((cert_host, port, proto))
                                        logs.logger.info(f'Added {proto}://{cert_host}:{port} to discoveries (from certificate)')
            sock.close()

        # NOTE: Add target based on resolved name for an IP address (even if not reachable, could change location)
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            try:
                response = self.nameserver.resolve_address(host)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.NoAnswer, dns.exception.Timeout):
                logs.logger.debug(f'Could not resolve {host}')
            else:
                try:
                    fqdn = list(response.rrset.items.keys())[0].to_text().rstrip('.')
                except KeyError:
                    pass
                else:
                    fqdn_host = fqdn.lower()
                    logs.logger.debug(f'Added {proto}://{fqdn_host}:{port} to discoveries (from resolver)')
                    self.discovered.add((fqdn_host, port, proto))

    def get_discovery_targets(self, targets, services):
        result = list()
        for target in targets:
            if all(target):
                result.append(target)
            else:
                host, port, proto = target
                if port is None and proto:
                    result.append((host, self.PROTO_PORTS[proto], proto))
                else:
                    for port, proto in services:
                        result.append((host, port, proto))
        return set(result)

    def get_final_targets(self, targets, services):
        discovery_targets = self.get_discovery_targets(targets, services)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(self.discover, target) for target in discovery_targets
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception as exc:
                    logs.logger.debug(f'Exception: {exc}')
        result = self.discovered.unique()
        if self.randomize:
            random.shuffle(result)
        return result

    def run(self, targets, services):
        final_targets = self.get_final_targets(targets, services)
        modules = [mods.Screens(self), mods.Response(self)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(module.execute, self.get_url(*target)) for module in modules for target in final_targets
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception as exc:
                    logs.logger.debug(f'Exception: {exc}')
        logs.logger.info(f'Finished, results in: {self.output_dir}')

    def parse(self, args):
        parser = self.get_parser()
        parsed = parser.parse_args(args)
        logs.init(parsed.loglevel)
        self.browser = parsed.browser
        self.nameserver.nameservers = [parsed.nameserver]
        self.randomize = parsed.randomize
        self.output_dir = parsed.output_dir
        if parsed.socks_proxy:
            socks_split = parsed.socks_proxy.split(':')
            self.socks_proxy = (socks_split[0], int(socks_split[1]))
        self.user_agent = parsed.user_agent
        self.headers['User-Agent'] = self.user_agent
        self.workers = parsed.workers
        self.process_timeout = parsed.process_timeout
        self.socket_timeout = parsed.socket_timeout
        if parsed.network:
            targets = self.targets_from_cidr(parsed.network)
        else:
            targets = self.targets_from_file(parsed.targets)
        ports = parsed.ports.split(',')
        services = [(int(service[0]), service[2]) for port in ports if (service := port.partition('/'))]
        self.run(targets, services)
