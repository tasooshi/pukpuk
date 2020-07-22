import os
import subprocess

from PIL import Image

from pukpuk.core.mods import HttpModule
from pukpuk.core import logging


class Module(HttpModule):

    name = 'Grabber'

    def execute(self, url):
        user_agent = self.args['user_agent']
        executable = self.args['executable']
        base_filename = self.get_base_filename(url, self.main.now)
        image_filename = base_filename + '.png'
        try:
            subprocess.check_output(
                [executable, '--headless', '--disable-gpu', '--window-size=1280,1696', '--v0', f'--screenshot={image_filename}', f'--user-agent={user_agent}', url],
                stderr=subprocess.STDOUT,
                timeout=self.args['process_timeout']
            )
        except FileNotFoundError:
            logging.logger.error(f'Error. Is {executable} installed?')
            exit(1)
        except subprocess.TimeoutExpired:
            logging.logger.info(f'Screen grabbing timed out for {url} (try adjusting --process-timeout)')
        else:
            with Image.open(image_filename) as img:
                extrema = img.convert('L').getextrema()
            if extrema[0] == extrema[1]:
                os.remove(image_filename)
                logging.logger.info(f'Blank screen for {url} returned, deleting image')
            logging.logger.info(f'Processed {url}')

    def extra_args(self, parser):
        super().extra_args(parser)
