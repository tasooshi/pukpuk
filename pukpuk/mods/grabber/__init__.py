import os
import pathlib
import subprocess

from PIL import Image

from pukpuk.core.mods import HttpModule
from pukpuk.core import logging


class Module(HttpModule):

    name = 'Grabber'

    def before(self):
        if self.main.proxy:
            self.cache['proxy_server'] = 'socks5://{}:{}'.format(*self.main.proxy)

    def execute(self, url):
        user_agent = self.args['user_agent']
        executable = self.args['executable']
        mod_dir = pathlib.Path(self.args['output_directory'], self.name.lower())
        mod_dir.mkdir(parents=True, exist_ok=True)
        base_filename = pathlib.Path(mod_dir, self.get_base_filename(url))
        image_filename = str(base_filename) + '.png'
        exec_args = [
            executable,
            '--headless',
            '--disable-gpu',
            '--window-size=1280,1696',
            '--v0',
            f'--screenshot={image_filename}',
            f'--user-agent="{user_agent}"',
            url,
        ]
        if self.main.proxy:
            exec_args.insert(len(exec_args) - 1, '--proxy-server="{}"'.format(self.cache['proxy_server']))
            exec_args.insert(len(exec_args) - 1, '--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE {}"'.format(self.main.proxy[0]))
        try:
            subprocess.check_output(
                exec_args,
                stderr=subprocess.STDOUT,
                timeout=self.args['process_timeout']
            )
        except FileNotFoundError:
            logging.logger.error(f'Error occured when grabbing the screen. Is `{executable}` installed?')
            exit(1)
        except subprocess.TimeoutExpired:
            logging.logger.debug(f'Screen grabbing timed out for {url} (try adjusting --process-timeout)')
        else:
            with Image.open(image_filename) as img:
                extrema = img.convert('L').getextrema()
            if extrema[0] == extrema[1]:
                os.remove(image_filename)
                logging.logger.debug(f'Blank screen for {url} returned, deleting image')
            logging.logger.info(f'{self.name} finished {url}')

    def extra_args(self, parser):
        super().extra_args(parser)
