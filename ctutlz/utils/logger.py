import logging
import sys

logger = logging.getLogger('ctutlz')

VERBOSE = 15


def init_logger():
    logging.addLevelName(VERBOSE, "VERBOSE")

    def info_verbose(self, message, *args, **kws):
        self.log(VERBOSE, message, *args, **kws)

    logging.Logger.verbose = info_verbose


def setup_logging(loglevel):
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
