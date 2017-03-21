import logging
import sys
from contextlib import contextmanager


@contextmanager
def loglevel(level):
    logger = logging.getLogger('ctutlz')
    levels = {}
    for handler in logger.handlers:
        levels[handler] = handler.level
        handler.setLevel(level)
    yield
    for handler in logger.handlers:
        handler.setLevel(levels[handler])


def setup_logging(loglevel):
    logger = logging.getLogger('ctutlz')
    logger.setLevel(logging.DEBUG)
    try:
        # python 2.6
        handler = logging.StreamHandler(stream=sys.stdout)
    except TypeError:
        # since python 2.7
        handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    return logger
