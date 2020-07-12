import asyncio

from pukpuk.core.logging import logger


class BaseModule:

    def init(self, args):
        logger.debug(f'Initializing {self.__module__}')
        self.args = args
        self.main = None

    def execute(self, main):
        self.main = main
        self.main.loop.run_until_complete(asyncio.gather(
            *[self.main.loop.run_in_executor(
                self.main.executor, self._execute, url
            ) for url in self.main.final_todos]
        ))

    def extra_args(self, parser):
        pass
