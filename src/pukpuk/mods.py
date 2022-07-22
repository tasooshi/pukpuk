import pathlib
import subprocess
import sys

import requests
from PIL import Image

from pukpuk import logs


class BaseModule:

    def __init__(self, app):
        self.name = type(self).__name__
        self.app = app
        self.output_dir = self.app.output_dir

    def get_base_dir(self):
        base_dir = pathlib.Path(self.output_dir, self.name.lower())
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def get_base_filename(self, url):
        return url.replace('://', '-').replace(':', '-')[:-1]


class Screens(BaseModule):

    def execute(self, url):
        browser = self.app.browser
        image_filename = str(pathlib.Path(self.get_base_dir(), self.get_base_filename(url))) + '.png'
        exec_args = [
            browser,
            '--headless',
            '--disable-gpu',
            '--window-size=1280,1696',
            '--v0',
            '--ignore-certificate-errors',
            f'--screenshot={image_filename}',
            f'--user-agent="{self.app.user_agent}"',
            url,
        ]
        try:
            output = subprocess.check_output(
                exec_args,
                stderr=subprocess.STDOUT,
                timeout=self.app.process_timeout
            )
            logs.logger.debug(output)
        except FileNotFoundError:
            logs.logger.error(f'Error occured when grabbing the screen. Is `{browser}` installed?')
            sys.exit(1)
        except subprocess.TimeoutExpired:
            logs.logger.debug(f'Screen grabbing timed out for {url} (try adjusting --process-timeout)')
        else:
            with Image.open(image_filename) as img:
                extrema = img.convert('L').getextrema()
            if extrema[0] == extrema[1]:
                pathlib.Path(image_filename).unlink()
                logs.logger.debug(f'Blank screen for {url} returned, deleting image')
            else:
                logs.logger.info(f'Saved {image_filename}')


class Responses(BaseModule):

    def execute(self, url):
        base_filename = pathlib.Path(self.get_base_dir(), self.get_base_filename(url) + '.txt')
        get_args = {
            'verify': False,
            'timeout': self.app.socket_timeout,
            'headers': self.app.headers,
        }
        try:
            response = requests.get(url, **get_args)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            logs.logger.debug(f'Could not retrieve {url}')
        except requests.exceptions.InvalidURL:
            logs.logger.debug(f'Invalid URL: {url}')
        else:
            with open(base_filename, 'wb') as fil:
                fil.write('\n'.join([header + ': ' + value for header, value in response.headers.items()]).encode('utf8'))
                fil.write('\n\n'.encode('utf8'))
                fil.write(response.content)
            logs.logger.info(f'Saved {base_filename}')
