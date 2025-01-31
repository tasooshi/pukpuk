import hashlib
import pathlib
import subprocess
import sys
from urllib import parse

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
        parsed = parse.urlparse(url)
        result = f'{parsed.scheme}-{parsed.hostname}'
        if parsed.port:
            result += f'-{parsed.port}'
        if parsed.path:
            result += '-' + hashlib.md5(parsed.path.encode('ascii')).hexdigest()
        return result


class Screens(BaseModule):

    def execute(self, url):
        browser = self.app.browser
        image_filename = str(pathlib.Path(self.get_base_dir(), self.get_base_filename(url))) + '.png'
        exec_args = [
            browser,
            '--headless',
            '--disable-gpu',
            '--window-size=1000,1000',
            '--v0',
            '--ignore-certificate-errors',
            '--run-all-compositor-stages-before-draw',
            f'--virtual-time-budget={self.app.time_budget}',
            f'--screenshot={image_filename}',
            f'--user-agent="{self.app.user_agent}"',
            url,
        ]
        for attempt in range(1, self.app.attempts + 1):
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
                logs.logger.debug(f'Screen grabbing timed out for {url} (attempt {attempt}/{self.app.attempts}, try adjusting --process-timeout)')
            else:
                with Image.open(image_filename) as img:
                    extrema = img.convert('L').getextrema()
                if extrema[0] == extrema[1]:
                    pathlib.Path(image_filename).unlink()
                    logs.logger.debug(f'Blank screen for {url} returned, deleting image')
                else:
                    logs.logger.info(f'Saved {image_filename}')
                break


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
            request_header = 'REQUEST'
            response_header = '\n\nRESPONSE'
            request = response.request
            output = [request_header, '=' * len(request_header), '\n', f'{request.method} {request.url}', '\n']
            output.extend([header + ': ' + value for header, value in request.headers.items()])
            output.extend([response_header, '=' * len(response_header), '\n'])
            output.extend([header + ': ' + value for header, value in response.headers.items()])
            output.append('\n')
            output.append(response.content.decode(response.encoding))
            pathlib.Path(base_filename).write_text('\n'.join(output))
            logs.logger.info(f'Saved {base_filename}')
