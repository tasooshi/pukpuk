import argparse
import atexit
import concurrent.futures
import concurrent.futures.thread
import errno
import pathlib
import random
import socket
import ssl
import sys
import threading
from datetime import datetime

import dns.exception
import dns.resolver
import dns.reversename
import netaddr
import requests
import urllib3
from OpenSSL import crypto

from pukpuk import (
    logs,
    mods,
    version,
)


class ParserError(Exception):

    pass


class CustomArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        raise ParserError(message)


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
    OUTPUT_URLS_FILENAME = 'urls.txt'
    DEFAULT_BROWSER = 'chromium'
    DEFAULT_PORTS = ('80/http', '443/https')
    DEFAULT_WORKERS = 15
    DEFAULT_PROCESS_TIMEOUT = 20
    DEFAULT_SOCKET_TIMEOUT = 3
    DEFAULT_GRABBING_ATTEMPTS = 3

    def __init__(
        self,
        ports=None,
        browser=None,
        randomize=False,
        user_agent=None,
        workers=None,
        output_dir=None,
        process_timeout=None,
        socket_timeout=None,
        skip_screens=False,
        attempts=None
    ):
        self.patch()
        self.browser = self.DEFAULT_BROWSER if browser is None else browser
        self.randomize = randomize
        self.skip_screens = skip_screens
        self.ports = list(self.DEFAULT_PORTS) if ports is None else ports
        self.finished = None
        self.process_timeout = self.DEFAULT_PROCESS_TIMEOUT if process_timeout is None else process_timeout
        self.socket_timeout = self.DEFAULT_SOCKET_TIMEOUT if socket_timeout is None else socket_timeout
        self.time_budget = int(self.process_timeout * 1000)
        self.nameserver = dns.resolver.Resolver(configure=True)
        self.nameserver.timeout = self.socket_timeout
        self.workers = self.DEFAULT_WORKERS if workers is None else workers
        self.attempts = self.DEFAULT_GRABBING_ATTEMPTS if attempts is None else attempts
        self.headers = requests.utils.default_headers()
        self.user_agent = self.headers['User-Agent'] if user_agent is None else user_agent
        self.output_dir = self.get_output_dir() if output_dir is None else output_dir
        self.discovered = Results()
        self.urls = list()
        self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE
        self.modules = None

    def get_parser(self):
        parser = CustomArgumentParser(
            prog='pukpuk',
            description='HTTP discovery and change monitoring tool',
            epilog=(
                'Examples:\n\n'
                '\t$ pukpuk -H hosts.txt\n\n'
                '\t$ pukpuk -U urls.txt\n\n'
                '\t$ pukpuk -N 192.168.1.0/24 -p 80/http,81/http,82/http,8080/http,8000/http,8888,443/https,8443,4443/https\n\n'
                '---'
                '\n\n'
            ),
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.print_usage = parser.print_help
        parser.add_argument('-N', '--network', help='Accepts network in CIDR notation or an IP range and performs discovery using ports in `-p`, e.g. "10.0.0.0/24", "10.0.1.1-10.2.1.1"')
        parser.add_argument('-H', '--hosts', help='Loads hosts from a file and performs discovery using ports in `-p`')
        parser.add_argument('-U', '--urls', help='Loads specific URLs from a file, skips discovery and ignores the `-p` argument for these')
        parser.add_argument('-p', '--ports', default=','.join(self.ports), help='Comma separated port list for HTTP service discovery [Default: ' + ', '.join(self.ports) + ']')
        parser.add_argument('-b', '--browser', default=self.browser, help='Chromium browser path for headless screen grabbing [Default: ' + self.browser + ']')
        parser.add_argument('-r', '--randomize', action='store_true', default=self.randomize, help='Randomize scanning order')
        parser.add_argument('-o', '--output-dir', default=self.output_dir, help='Path where results (text files, images) will be stored [Default: ' + self.output_dir + ']')
        parser.add_argument('-u', '--user-agent', default=self.user_agent, help='Browser User-Agent header [Default: ' + self.user_agent + ']')
        parser.add_argument('-w', '--workers', default=self.workers, type=int, help='Number of concurrent workers [Default: ' + str(self.workers) + ']')
        parser.add_argument('--process-timeout', type=float, default=self.process_timeout, help='Process timeout in seconds [Default: ' + str(self.process_timeout) + ']')
        parser.add_argument('--socket-timeout', type=float, default=self.socket_timeout, help='Socket timeout in seconds [Default: ' + str(self.socket_timeout) + ']')
        parser.add_argument('--skip-screens', action='store_true', default=self.skip_screens, help='Skip screen grabbing')
        parser.add_argument('--grabbing-attempts', default=self.attempts, type=int, help='Number of screen grabbing attempts [Default: ' + str(self.attempts) + ']')
        parser.add_argument('-v', '--version', action='version', version=version.__version__, help='Print version')
        verbosity = parser.add_mutually_exclusive_group()
        verbosity.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logs.logging.DEBUG, default=logs.logging.INFO)
        verbosity.add_argument('-q', '--quiet', action='store_const', dest='loglevel', const=logs.logging.NOTSET, default=logs.logging.INFO)
        return parser

    def patch(self):
        logs.logger.debug(f'Patching')
        urllib3.disable_warnings()
        atexit.unregister(concurrent.futures.thread._python_exit)

    def targets_from_network(self, network):
        """Converts network string to list of IP addresses

        """
        logs.logger.debug(f'Targets from `network` argument: {network}')
        ips = None
        try:
            ips = netaddr.IPNetwork(network)
        except (netaddr.core.AddrFormatError, ValueError):
            pass
        try:
            ips = netaddr.iter_iprange(*network.split('-'))
        except TypeError:
            pass
        if ips:
            for ip in ips:
                yield (str(ip), None, None)
        else:
            logs.logger.error(f'Invalid `network` argument: {network}')
            sys.exit(errno.EINVAL)

    def targets_from_file(self, path):
        """Loads list of IP addresses and host names from a text file

        """
        logs.logger.debug(f'Targets from file `{path}`')
        with open(path) as fil:
            for line in fil:
                yield (line.strip(), None, None)

    def urls_from_file(self, path):
        """Loads list of URLs from a text file

        """
        logs.logger.debug(f'URLs from file `{path}`')
        with open(path) as fil:
            for line in fil:
                yield line.strip()

    def get_url(self, host, port, proto):
        """Converts (host, port, protocol) tuple to URL

        """
        return f'{proto}://{host}:{port}'

    def get_output_dir(self):
        name_date = datetime.now().strftime('%Y%m%d_%H%M')
        name = name_date + self.OUTPUT_DIR_EXT
        suffix = 0
        while pathlib.Path(name).exists():
            suffix += 1
            name = name_date + '-' + str(suffix) + self.OUTPUT_DIR_EXT
        logs.logger.debug(f'Output directory `{name}`')
        return name

    def sock_connect(self, host, port):
        logs.logger.debug(f'Connecting to `{host}:{port}`')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.socket_timeout)
        try:
            sock.connect((host, port))
        except Exception as exc:
            logs.logger.debug(f'Error when connecting to `{host}:{port}`: {exc}')
        else:
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
            logs.logger.debug(f'Checking if `{host}:{port}` is encrypted')
            sock = self.sock_connect(host, port)
            try:
                ssock = self.ssl_ctx.wrap_socket(sock, server_hostname=host)
                ssock.getpeercert(True)
            except (ConnectionResetError, socket.timeout, ssl.SSLError):
                logs.logger.debug(f'Probably not encrypted `{host}:{port}`')
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
        logs.logger.debug(f'Discovering `{target}`')
        host, port, proto = target
        if not proto:
            proto = self.port_test(host, port)

        if proto is self.PROTO_UNKNOWN:
            return

        sock = self.sock_connect(host, port)
        if sock:
            self.discovered.add((host, port, proto))
            logs.logger.info(f'Added `{proto}://{host}:{port}` to discoveries')
            # NOTE: If HTTPS extract certificate details and add all extra host names to the list
            if proto == self.PROTO_HTTPS:
                try:
                    ssock = self.ssl_ctx.wrap_socket(sock, server_hostname=host)
                    cert = ssock.getpeercert(True)
                except (OSError, ConnectionResetError, socket.timeout, ssl.SSLError):
                    logs.logger.debug(f'Probably not encrypted `{host}:{port}`')
                else:
                    logs.logger.debug(f'Parsing certificate for `{host}:{port}`')
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
                                        if cert_host != host:
                                            self.discovered.add((cert_host, port, proto))
                                            logs.logger.info(f'Added `{proto}://{cert_host}:{port}` to discoveries (from certificate)')
            try:
                netaddr.IPAddress(host)
            except netaddr.core.AddrFormatError:
                logs.logger.debug(f'`{host}` is not IP address')
            else:
                try:
                    response = self.nameserver.resolve_address(host)
                except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.NoAnswer, dns.exception.Timeout):
                    logs.logger.debug(f'Could not resolve `{host}`')
                else:
                    try:
                        fqdn = list(response.rrset.items.keys())[0].to_text().rstrip('.')
                    except KeyError:
                        pass
                    else:
                        fqdn_host = fqdn.lower()
                        logs.logger.info(f'Added `{proto}://{fqdn_host}:{port}` to discoveries (from resolver)')
                        self.discovered.add((fqdn_host, port, proto))
            sock.close()

    def get_discovery_targets(self, targets, services):
        discovery_targets = list()
        for target in targets:
            if all(target):
                discovery_targets.append(target)
            else:
                host, port, proto = target
                if port is None and proto:
                    discovery_targets.append((host, self.PROTO_PORTS[proto], proto))
                else:
                    for port, proto in services:
                        discovery_targets.append((host, port, proto))
        discovery_targets = set(discovery_targets)
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

    def execute(self, url):
        for module in self.modules:
            module.execute(url)

    def run(self, targets, services=None):
        self.finished = False
        self.modules = [
            mods.Responses(self),
        ]
        if not self.skip_screens:
            self.modules.append(mods.Screens(self))
        if self.randomize:
            random.shuffle(targets)
            random.shuffle(services)
        logs.logger.info(f'Discovery in progress')
        discovery_targets = self.get_discovery_targets(targets, services)
        self.urls.extend([self.get_url(*target) for target in discovery_targets])
        if self.urls:
            logs.logger.info(f'Discovery finished, running modules')
        else:
            logs.logger.info(f'Nothing to do!')
            sys.exit()
        pathlib.Path(self.output_dir, self.OUTPUT_URLS_FILENAME).write_text('\n'.join(self.urls))
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(self.execute, url) for url in self.urls
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception as exc:
                    logs.logger.debug(f'Exception: {exc}')
        self.finished = True
        logs.logger.info(f'Finished, results in `{self.output_dir}`')

    def parse(self, args):
        parser = self.get_parser()
        try:
            parsed = parser.parse_args(args)
        except ParserError as exc:
            logs.logger.error(f'Error: {exc}')
            sys.exit(errno.EINVAL)
        pathlib.Path(parsed.output_dir).mkdir(parents=True, exist_ok=True)
        logs.init(parsed.loglevel, parsed.output_dir)
        self.browser = parsed.browser
        self.randomize = parsed.randomize
        self.attempts = parsed.grabbing_attempts
        self.skip_screens = parsed.skip_screens
        self.output_dir = parsed.output_dir
        self.user_agent = parsed.user_agent
        self.headers['User-Agent'] = self.user_agent
        self.workers = parsed.workers
        self.process_timeout = parsed.process_timeout
        self.socket_timeout = parsed.socket_timeout
        # NOTE: Skip discovery for URLs provided in a file
        if parsed.urls:
            self.urls.extend(self.urls_from_file(parsed.urls))
        ports = parsed.ports.split(',')
        services = [(int(service[0]), service[2]) for port in ports if (service := port.partition('/'))]
        for service in services:
            proto = service[1] if service[1] else self.PROTO_UNKNOWN
            if proto and proto not in (self.PROTO_HTTP, self.PROTO_HTTPS):
                logs.logger.error(f'Error: invalid service `{proto}`')
                sys.exit(errno.EINVAL)
        targets = list()
        if parsed.network:
            targets.extend(self.targets_from_network(parsed.network))
        if parsed.hosts:
            targets.extend(self.targets_from_file(parsed.hosts))
        self.run(targets, services)
