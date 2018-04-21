'''Download all leave entries from one or more CT-Logs.'''

import argparse
import logging
import os
import os.path
from pprint import pformat

import utlz
from utlz import flo

from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger
from ctutlz.grabctlog.ctlog_grabber import grab_ctlogs, ctlog_dir_for, STEP_SIZE


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

    parser.add_argument('--show',
                        action='store_true',
                        default=False,
                        help='show if grabbed data of ctlog given by url is '
                             'complete (and do not grab entries)')

    parser.add_argument('--to',
                        default=os.getcwd(),
                        metavar='<dirname>',
                        help='base dir where grabbed ctlog data will be stored'
                             ' (default: current working dir)')

    return parser


def show_completion_states(uris, basedir):
    for uri in uris:
        ctlog_dir = ctlog_dir_for(basedir, uri)
        filename = os.path.join(ctlog_dir, 'get-sth.json')
        data = utlz.load_json(filename)
        tree_size = data['tree_size']

        complete = True
        num_incomplete = 0

        stop = tree_size
        step = STEP_SIZE

        for start in range(0, stop, step):
            end = start + step - 1  # eg. end = 9999
            if end >= tree_size:
                end = tree_size - 1

            fname = flo('get-entries-{start}-{end}.json')
            if not os.path.exists(os.path.join(ctlog_dir, fname)):
                num_incomplete += end - start + 1
                complete = False

        num_complete = tree_size - num_incomplete

        if complete:
            logger.info(flo(
                # 'complete: {uri}  [{tree_size:,}]'))  # TODO DEBUG
                'complete: {uri}  [{tree_size:,}] {num_complete}'))
        else:
            # percent_incomplete = num_incomplete / tree_size * 100
            percent_complete = num_complete / tree_size * 100
            logger.info(flo(
                'incomplete: {uri}  {num_complete:,} [{tree_size:,}]  '
                '{percent_complete:.2f} %'))


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

    if args.show:
        show_completion_states(uris, basedir)
    else:
        grab_ctlogs(uris, basedir)


if __name__ == '__main__':
    main()
