import logging
import pathlib


logger = logging.getLogger('pukpuk')
formatter = {
    logging.DEBUG: logging.Formatter('%(name)s %(levelname)s [%(asctime)s] %(message)s'),
    logging.INFO: logging.Formatter('[%(asctime)s] %(message)s'),
}
handler = logging.StreamHandler()
logger.addHandler(handler)


def init(loglevel, directory):
    logger.setLevel(loglevel)
    logger.addHandler(logging.FileHandler(filename=pathlib.Path(directory, 'pukpuk.log')))
    try:
        handler.setFormatter(formatter[loglevel])
    except KeyError:
        pass
