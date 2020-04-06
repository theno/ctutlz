'''Download, merge and summarize known logs for Certificate Transparency (CT).

Print output to stdout, warnings and errors to stderr.

The source of information is:
https://www.gstatic.com/ct/log_list/v2/all_logs_list.json

from page https://www.certificate-transparency.org/known-logs
'''

import argparse
import datetime
import json
import logging

from utlz import first_paragraph, flo, red

from ctutlz.ctlog import download_log_list
from ctutlz.ctlog import set_operator_names, print_schema
from ctutlz.ctlog import URL_ALL_LOGS, Logs
from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger
from ctutlz._version import __version__


def create_parser():
    parser = argparse.ArgumentParser(description=first_paragraph(__doc__))
    parser.epilog = __doc__.split('\n', 1)[-1]
    parser.add_argument('-v', '--version',
                        action='version',
                        default=False,
                        version=__version__,
                        help='print version number')

    me1 = parser.add_mutually_exclusive_group()
    me1.add_argument('--short',
                     dest='loglevel',
                     action='store_const',
                     const=logging.INFO,
                     default=VERBOSE,  # default loglevel if nothing set
                     help='show short results')
    me1.add_argument('--debug',
                     dest='loglevel',
                     action='store_const',
                     const=logging.DEBUG,
                     help='show more for diagnostic purposes')

    me2 = parser.add_mutually_exclusive_group()
    me2.add_argument('--json',
                     action='store_true',
                     dest='print_json',
                     help='print merged log lists as json')
    me2.add_argument('--schema',
                     action='store_true',
                     dest='print_schema',
                     help='print json schema')
    return parser


def warn_inconsistency(url, val_a, val_b):

    # suppress warning doubles (i know it's hacky)
    key = flo('{url}' + ''.join(sorted(flo('{val_a}{val_b}'))))
    if not hasattr(warn_inconsistency, 'seen'):
        warn_inconsistency.seen = {}
    if not warn_inconsistency.seen.get(key, False):
        warn_inconsistency.seen[key] = True
    else:
        return

    logger.warning(red(flo(
        'inconsistent data for log {url}: {val_a} != {val_b}')))


def data_structure_from_log(log):
    log_data = dict(log._asdict())

    log_data['id_b64'] = log.id_b64
    log_data['pubkey'] = log.pubkey
    log_data['scts_accepted_by_chrome'] = \
        log.scts_accepted_by_chrome

    return log_data


def list_from_lists(log_lists):
    log_list = []
    for item_dict in log_lists:
        for log in item_dict['logs']:
            log_data = data_structure_from_log(log)
            log_list.append(log_data)
    return log_list


def show_log(log, order=3):
    logger.verbose('#'*order + flo(' {log.url}\n'))

    logdict = log._asdict()

    for key, value in logdict.items():
        if key == 'id_b64_non_calculated' and value == log.id_b64:
            value = None  # don't log this value
        if key == 'operated_by':
            value = ', '.join(value)
        # avoid markdown syntax interpretation and improve readablity
        key = key.replace('_', ' ')
        if value is not None:
            logger.verbose(flo('* __{key}__: `{value}`'))

    logger.verbose(flo('* __scts accepted by chrome__: '
                       '{log.scts_accepted_by_chrome}'))

    if log.key is not None:
        logger.verbose(flo('* __id b64__: `{log.log_id}`'))
        logger.verbose(flo('* __pubkey__:\n```\n{log.pubkey}\n```'))

    logger.verbose('')


def show_logs(logs, heading, order=2):
    if len(logs) <= 0:
        return

    logger.info('#' * order + '%s\n' % ' ' + heading if heading else '')
    s_or_not = 's'
    if len(logs) == 1:
        s_or_not = ''
    # show log size
    logger.info('%i log%s\n' % (len(logs), s_or_not))

    # list log urls
    for log in logs:
        if logger.level < logging.INFO:
            anchor = log.url.replace('/', '')
            logger.verbose('* [%s](#%s)' % (log.url, anchor))
        else:
            logger.info('* %s' % log.url)
    logger.info('')
    for log in logs:
        show_log(log)

    logger.info('End of list')


def ctloglist(print_json=None):
    '''Gather ct-log lists and print the merged log list.

    Args:
        print_json(boolean): If True, print merged log list as json data.
                             Else print as markdown.
    '''
    if not print_json:
        today = datetime.date.today()
        now = datetime.datetime.now()

        logger.info('# Known Certificate Transparency (CT) Logs\n')
        logger.verbose('Created with [ctloglist]'
                       '(https://github.com/theno/ctutlz#ctloglist)\n')
        logger.verbose('* [all_logs_list.json]('
                       'https://www.gstatic.com/ct/log_list/v2/all_logs_list.json)'
                       '\n')
        logger.info(flo('Version (Date): {today}\n'))
        logger.verbose(flo('Datetime: {now}\n'))
        logger.info('')  # formatting: insert empty line

    # all_logs_list.json

    all_dict = download_log_list(URL_ALL_LOGS)
    orig_all_dict = dict(all_dict)
    set_operator_names(all_dict)

    all_logs = Logs([all_dict])

    if print_json:

        json_str = json.dumps(orig_all_dict, indent=4, sort_keys=True)
        print(json_str)

    else:
        show_logs(all_logs, '')


def main():
    init_logger()
    parser = create_parser()
    args = parser.parse_args()
    setup_logging(args.loglevel)
    logger.debug(args)
    if args.print_schema:
        print_schema()
    else:
        ctloglist(args.print_json)


if __name__ == '__main__':
    main()
