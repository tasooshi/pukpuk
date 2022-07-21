import logging


logger = logging.getLogger('pukpuk')
formatter = {
    logging.DEBUG: logging.Formatter('%(name)s %(levelname)s [%(asctime)s] %(message)s'),
    logging.INFO: logging.Formatter('[%(asctime)s] %(message)s'),
}
handler = logging.StreamHandler()
logger.addHandler(handler)


def init(loglevel):
    logger.setLevel(loglevel)
    try:
        handler.setFormatter(formatter[loglevel])
    except KeyError:
        pass
