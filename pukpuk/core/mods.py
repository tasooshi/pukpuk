from pukpuk.core.logging import logger


class BaseModule:

    def init(self, args, main):
        logger.debug(f'Initializing {self.__module__}')
        self.args = args
        self.main = main

    def execute(self):
        raise NotImplementedError

    def extra_args(self, parser):
        pass


class HttpModule(BaseModule):

    def get_base_filename(self, url, time):
        return url.replace('://', '-').replace(':', '-')[:-1] + '-' + time.strftime('%Y%m%d_%H%M')
