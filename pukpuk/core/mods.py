from pukpuk.core.logging import logger


class BaseModule:

    def __init__(self, *args, **kwargs):
        self.args = None
        self.main = None
        self.cache = dict()

    def init(self, args, main):
        logger.debug(f'Initializing {self.__module__}')
        self.args = args
        self.main = main
        self.before()

    def before(self):
        pass

    def execute(self):
        raise NotImplementedError

    def extra_args(self, parser):
        pass


class HttpModule(BaseModule):

    def get_base_filename(self, url):
        return url.replace('://', '-').replace(':', '-')[:-1]
