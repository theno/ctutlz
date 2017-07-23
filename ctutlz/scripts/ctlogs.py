'''Identify and summarize known logs for Certificate Transparency (CT).

Currently there exist three log lists with differing infos:

1. listing of webpage https://www.certificate-transparency.org/known-logs
2. log_list.json
3. all_logs_list.json.

This three log lists will be merged into one list in the future.  Diskussion:
https://groups.google.com/forum/?fromgroups#!topic/certificate-transparency/zBv7EK0522w
'''

import argparse
import logging

from utlz import first_paragraph

from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger
from ctutlz._version import __version__


def create_parser():
    parser = argparse.ArgumentParser(description=first_paragraph(__doc__))
    parser.add_argument('-v', '--version',
                        action='version',
                        default=False,
                        version=__version__,
                        help='print version number')

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument('--short',
                     dest='loglevel',
                     action='store_const',
                     const=logging.INFO,
                     default=VERBOSE,  # default loglevel if nothing set
                     help='show short results and warnings/errors only')
    meg.add_argument('--debug',
                     dest='loglevel',
                     action='store_const',
                     const=logging.DEBUG,
                     help='show more for diagnostic purposes')
    parser.epilog = __doc__.split('\n', maxsplit=1)[-1]
    return parser


def main():
    init_logger()
    parser = create_parser()
    args = parser.parse_args()
    setup_logging(args.loglevel)
    logger.debug(args)

    # TODO implementation


if __name__ == '__main__':
    main()
