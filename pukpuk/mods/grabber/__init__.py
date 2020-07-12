import subprocess

from pukpuk.core.mods import BaseModule
from pukpuk.core import logging


class Module(BaseModule):

    name = 'Grabber'

    def _execute(self, url):
        base_filename = url.replace('://', '_').replace(':', '-')[:-1] + '-' + self.main.now.strftime('%Y%m%d_%H%M')
        user_agent = self.args['user_agent']
        executable = self.args['executable']
        try:
            subprocess.check_output(
                [executable, '--headless', '--disable-gpu', '--window-size=1280,1696', '--v0', f'--screenshot={base_filename}.png', f'--user-agent={user_agent}', url],
                stderr=subprocess.STDOUT,
                timeout=self.args['process_timeout']
            )
        except FileNotFoundError:
            logging.logger.error(f'Error. Is {executable} installed?')
            exit(1)
        except subprocess.TimeoutExpired:
            logging.logger.info(f'Screen grabbing timed out for {url} (try adjusting --process-timeout)')
        else:
            logging.logger.info(f'Processed {url}')

    def extra_args(self, parser):
        super().extra_args(parser)
