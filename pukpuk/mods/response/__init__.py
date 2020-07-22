import requests

from pukpuk.core.mods import HttpModule
from pukpuk.core import logging


class Module(HttpModule):

    name = 'Response'

    def execute(self, url):
        base_filename = self.get_base_filename(url, self.main.now)
        try:
            response = requests.get(url, verify=False, timeout=self.args['socket_timeout'], headers=self.main.headers)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            logging.logger.info(f'Could not retrieve {url} (screen grabbing skipped)')
        except requests.exceptions.InvalidURL:
            logging.logger.info(f'Invalid URL: {url} (screen grabbing skipped)')
        else:
            with open(f'{base_filename}.txt', 'wb') as fil:
                fil.write('\n'.join([header + ': ' + value for header, value in response.headers.items()]).encode('utf8'))
                fil.write('\n\n'.encode('utf8'))
                fil.write(response.content)
            logging.logger.info(f'Processed {url}')

    def extra_args(self, parser):
        super().extra_args(parser)
