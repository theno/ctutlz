import logging
import sys

logger = logging.getLogger('ctutlz')

VERBOSE = 15  # between DEBUG=10 and INFO=20


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, VERBOSE, logging.INFO)


def init_logger():
    logging.addLevelName(VERBOSE, "VERBOSE")

    def info_verbose(self, message, *args, **kws):
        self.log(VERBOSE, message, *args, **kws)

    logging.Logger.verbose = info_verbose


def setup_logging(loglevel):
    '''Write info, verbose and debug messages to stdout, else to stderr
    (warning and error).
    '''
    logger.setLevel(loglevel)
    try:
        # python 2.6
        out_handler = logging.StreamHandler(stream=sys.stdout)
        err_handler = logging.StreamHandler(stream=sys.stderr)
    except TypeError:
        # since python 2.7
        out_handler = logging.StreamHandler()
        err_handler = logging.StreamHandler(stream=sys.stderr)

    out_handler.setLevel(loglevel)
    out_handler.addFilter(InfoFilter())

    err_handler.setLevel(logging.WARNING)

    logger.addHandler(out_handler)
    logger.addHandler(err_handler)

    return logger
