from pukpuk.core.logging import logger


class BaseModule:

    def __init__(self, *args, **kwargs):
        self.main = None
        self.cache = dict()

    def init(self, main):
        logger.debug(f'Initializing {self.__module__}')
        self.main = main
        self.before()

    def before(self):
        pass

    def execute(self):
        raise NotImplementedError


class HttpModule(BaseModule):

    def get_base_filename(self, url):
        return url.replace('://', '-').replace(':', '-')[:-1]
