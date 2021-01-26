import pathlib

import requests

from pukpuk.core.mods import HttpModule
from pukpuk.core import logging


class Module(HttpModule):

    name = 'Response'

    def before(self):
        if self.main.proxy:
            socks_str = f'socks5h://{self.main.proxy[0]}:{self.main.proxy[1]}'
            self.cache['proxies'] = {
                'http': socks_str,
                'https': socks_str,
            }

    def execute(self, url):
        mod_dir = pathlib.Path(self.main.args.output_directory, self.name.lower())
        mod_dir.mkdir(parents=True, exist_ok=True)
        base_filename = pathlib.Path(mod_dir, self.get_base_filename(url))
        get_args = {
            'verify': False,
            'timeout': self.main.args.socket_timeout,
            'headers': self.main.headers,
        }
        if self.main.proxy:
            get_args['proxies'] = self.cache['proxies']
        try:
            response = requests.get(url, **get_args)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            logging.logger.debug(f'Could not retrieve {url}')
        except requests.exceptions.InvalidURL:
            logging.logger.info(f'Invalid URL: {url}')
        else:
            with open(f'{base_filename}.txt', 'wb') as fil:
                fil.write('\n'.join([header + ': ' + value for header, value in response.headers.items()]).encode('utf8'))
                fil.write('\n\n'.encode('utf8'))
                fil.write(response.content)
            logging.logger.info(f'{self.name} finished {url}')
