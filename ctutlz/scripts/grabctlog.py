'''Download all leave entries from one or more CT-Logs.'''

import argparse
import logging
import os
import os.path
from pprint import pformat

import utlz
from utlz import flo

from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger

from ctutlz.grabctlog.ctlog_grabber import grab_ctlogs


def create_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url',
                        nargs='+',
                        help="url of CT-Log")

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

    parser.add_argument('--to',
                        default=os.getcwd(),
                        metavar='<dirname>',
                        help='base dir where grabbed ctlog data will be stored'
                             ' (default: current working dir)')

    return parser


def main():
    init_logger()
    parser = create_parser()
    args = parser.parse_args()
    setup_logging(args.loglevel)
    logger.debug(args)

    # assure uris have the same format as the "url" values in the
    # json log lists
    # eg. uris = ['ct.googleapis.com/testtube/', 'ct.googleapis.com/skydiver/']
    uris = ['{}/'.format(url.lstrip('https://').rstrip('/'))
            for url
            in args.url]

    basedir = os.path.abspath(os.path.expanduser(args.to))

    logger.debug(pformat(locals()))

    grab_ctlogs(uris, basedir)


if __name__ == '__main__':
    main()
