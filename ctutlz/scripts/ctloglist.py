'''Download, merge and summarize known logs for Certificate Transparency (CT).

Print output to stdout, warning and errors to stderr.

Currently there exist three log lists with differing infos:

1. listing of webpage https://www.certificate-transparency.org/known-logs
2. log_list.json
3. all_logs_list.json.

This three log lists will be merged into one list in the future.  Discussion:
https://groups.google.com/forum/?fromgroups#!topic/certificate-transparency/zBv7EK0522w
'''

import argparse
import datetime
import json
import logging

from utlz import first_paragraph, flo, red

from ctutlz.ctlog import logs_dict_from_webpage, download_log_list
from ctutlz.ctlog import set_operator_names, print_schema, unset_operator_names
from ctutlz.ctlog import URL_LOG_LIST, URL_ALL_LOGS, Log, Logs
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

    logger.warn(red(flo(
        'inconsistent data for log {url}: {val_a} != {val_b}')))


def merge_logs(log_a, log_b):
    '''Return two logs merged into one log.

    If two values exist for one key and the differ, take value of log_a and
    print out a warning (to stderr).

    Args:
        log_a (ctutlz.ctlog.Log)
        log_b (ctutlz.ctlog.Log)

    Return: ctutlz.ctlog.Log
    '''
    logdict_a = log_a._asdict()
    logdict_b = log_b._asdict()

    merged = {}

    for key, val_a in logdict_a.items():
        val_b = logdict_b[key]
        if val_a is None:
            merged[key] = val_b  # may be None or not
        else:
            if val_b is not None and val_a != val_b:
                warn_inconsistency(log_a.url, val_a, val_b)
            merged[key] = val_a

    nc_a = log_a.id_b64_non_calculated
    nc_b = log_b.id_b64_non_calculated
    if nc_a is not None:
        if nc_b is not None and nc_a != nc_b:
            warn_inconsistency(log_a.url, nc_a, nc_b)
        if log_b.id_b64 is not None and nc_a != log_b.id_b64:
            warn_inconsistency(log_a.url, nc_a, log_b.id_b64)
    if nc_b is not None and log_a.id_b64 is not None:
        if log_a.id_b64 != nc_b:
            warn_inconsistency(log_a.url, log_a.id_b64, nc_b)

    return Log(**merged)


def merge_log_list_r(list_a, list_b, merged_logs=[], unmerged_a=[]):
    '''Merge two log lists `list_a`, `list_b` merged by log url.'''
    if len(list_a) == 0:
        unmerged_b = list_b
        return (merged_logs, unmerged_a, unmerged_b)

    log_a = list_a[0]
    rest_a = list_a[1:]

    matches = [item
               for item in list_b
               if item.url.rstrip('/') == log_a.url.rstrip('/')]
    rest_b = [item
              for item in list_b
              if item.url.rstrip('/') != log_a.url.rstrip('/')]

    merged_log = None
    unmerged_log = None

    if matches:
        merged_log = log_a
        for log_b in matches:
            merged_log = merge_logs(merged_log, log_b)
    else:
        unmerged_log = log_a

    if merged_log:
        merged_logs = merged_logs + [merged_log]
    if unmerged_log:
        unmerged_a = unmerged_a + [unmerged_log]

    return merge_log_list_r(rest_a, rest_b, merged_logs, unmerged_a)


def merge_enrich_a_with_b(log_list_a, log_list_b):
    '''
    Differing log values in log_list_a win over log_list_b.
    '''
    merged, rest_a, rest_b = merge_log_list_r(log_list_a, log_list_b)
    return merged + rest_a, rest_b


def merge_overwrite_a_with_b(log_list_a, log_list_b):
    '''
    Differing log values in log_list_b win over log_list_a.
    '''
    merged, rest_b, rest_a = merge_log_list_r(log_list_b, log_list_a)
    return merged + rest_a, rest_b


def merge_log_lists(compliant_logs, all_logs,
                    active_from_webpage, frozen_from_webpage,
                    ceased_from_webpage, special_from_webpage, **_):
    '''Merge log lists and return merged logs.

    The problem here is that there are two kind of states (two state machines)
    which overlap:
     * chrome ct policy inclusion states:  ctutlz.ctlog.ChromeStates
     * log functionality states:           ctutlz.ctlog.Functions
    They should be combined into one kind of states.
    '''
    # log lists

    compliant_active = []
    compliant_frozen = []
    compliant_ceased = []
    compliant_special = []

    active_not_compliant = []
    frozen_not_compliant = []
    ceased_not_compliant = []
    special_not_compliant = []

    # merge log_list.json with log lists from webpage

    compliant_rest = compliant_logs  # chrome ct policy compliant: log_list.json

    compliant_active, compliant_rest, active_not_compliant = merge_log_list_r(
        compliant_rest, active_from_webpage)
    compliant_frozen, compliant_rest, frozen_not_compliant = merge_log_list_r(
        compliant_rest, frozen_from_webpage)
    compliant_ceased, compliant_rest, ceased_not_compliant = merge_log_list_r(
        compliant_rest, ceased_from_webpage)
    compliant_special, compliant_rest, special_not_compliant = merge_log_list_r(
        compliant_rest, special_from_webpage)

    # merge log lists with all_logs.json

    all_rest = all_logs  # all_logs.json

    compliant_active, all_rest = merge_enrich_a_with_b(compliant_active,
                                                       all_rest)
    compliant_frozen, all_rest = merge_enrich_a_with_b(compliant_frozen,
                                                       all_rest)
    compliant_ceased, all_rest = merge_enrich_a_with_b(compliant_ceased,
                                                       all_rest)
    compliant_special, all_rest = merge_enrich_a_with_b(compliant_special,
                                                        all_rest)
    compliant_rest, all_rest = merge_enrich_a_with_b(compliant_rest,
                                                     all_rest)

    active_not_compliant, all_rest = \
        merge_overwrite_a_with_b(active_not_compliant, all_rest)
    frozen_not_compliant, all_rest = \
        merge_overwrite_a_with_b(frozen_not_compliant, all_rest)
    ceased_not_compliant, all_rest = \
        merge_overwrite_a_with_b(ceased_not_compliant, all_rest)
    special_not_compliant, all_rest = \
        merge_overwrite_a_with_b(special_not_compliant, all_rest)

    # warn for missing logs on webpage

    for log in compliant_rest:
        logger.warn(red(flo(
            'chrome ct policy compliant log not listet on webpage: {log.url}')))

    for log in all_rest:
        logger.warn(red(flo(
            'log in all_logs.json not listed on webpage: {log.url}')))

    return [
        {'heading': 'compliant to chrome ct policy - active logs',
         'logs': compliant_active},
        {'heading': 'compliant to chrome ct policy - frozen logs',
         'logs': compliant_frozen},
        {'heading': 'compliant to chrome ct policy - ceased logs',
         'logs': compliant_ceased},
        {'heading': 'compliant to chrome ct policy - special purpose logs',
         'logs': compliant_special},

        {'heading': 'compliant to chrome ct policy - UNLISTED ON WEBPAGE',
         'logs': compliant_rest},

        {'heading': 'not compliant to chrome ct policy - active logs',
         'logs': active_not_compliant},
        {'heading': 'not compliant to chrome ct policy - frozen logs',
         'logs': frozen_not_compliant},
        {'heading': 'not compliant to chrome ct policy - ceased logs',
         'logs': ceased_not_compliant},
        {'heading': 'not compliant to chrome ct policy - special purpose logs',
         'logs': special_not_compliant},

        {'heading': 'not compliant to chrome ct policy - UNLISTED ON WEBPAGE',
         'logs': all_rest},
    ]


def data_structure_from_log(log):
    log_data = dict(log._asdict())

    log_data['id_b64'] = log.id_b64
    log_data['pubkey'] = log.pubkey
    log_data['compliant_to_chrome_ct_policy'] = \
        log.compliant_to_chrome_ct_policy

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

    if log.chrome_status is not None:
        logger.verbose(flo('* __compliant to chrome ct policy__: '
                           '{log.compliant_to_chrome_ct_policy}'))

    if log.key is not None:
        logger.verbose(flo('* __id b64__: `{log.id_b64}`'))
        logger.verbose(flo('* __pubkey__:\n```\n{log.pubkey}\n```'))

    logger.verbose('')


def show_logs(logs, heading, order=2):
    if len(logs) > 0:
        logger.info('#'*order + flo(' {heading}\n'))
        s_or_not = 's'
        if len(logs) == 1:
            s_or_not = ''
        # show log size
        logger.info('%i log%s\n' % (len(logs), s_or_not))

        # list log urls
        for log in logs:
            if logger.level < logging.INFO:
                anchor = log.url.replace('/', '')
                logger.verbose(flo('* [{log.url}](#{anchor})'))
            else:
                logger.info(flo('* {log.url}'))
        logger.info('')
        for log in logs:
            show_log(log)


def ctloglist(print_json=None):
    if not print_json:
        today = datetime.date.today()
        now = datetime.datetime.now()

        logger.info('# Known Certificate Transparency (CT) Logs\n')
        logger.verbose('https://www.certificate-transparency.org/known-logs\n')
        logger.info(flo('Version (Date): {today}\n'))
        logger.verbose(flo('Datetime: {now}\n'))
        logger.info('')  # formatting: insert empty line

    # from webpage

    webpage_dict = logs_dict_from_webpage()

    # active, frozen and ceased logs could be in compliant_logs, too
    active_from_webpage = Logs(webpage_dict['active_logs'])
    frozen_from_webpage = Logs(webpage_dict['frozen_logs'])
    ceased_from_webpage = Logs(webpage_dict['logs_that_ceased_operation'])

    special_from_webpage = Logs(webpage_dict['special_purpose_logs'])

    # log_list.json: chrome ct policy compliant logs

    compliant_dict = download_log_list(URL_LOG_LIST)
    set_operator_names(compliant_dict)

    compliant_logs = Logs(compliant_dict['logs'])

    # all_logs_list.json

    all_dict = download_log_list(URL_ALL_LOGS)
    set_operator_names(all_dict)

    all_logs = Logs(all_dict['logs'])

    log_lists = merge_log_lists(**locals())

    if print_json:
        data = {
            'operators': all_dict['operators'],
            'logs': list_from_lists(log_lists)
        }
        unset_operator_names(data)
        json_str = json.dumps(data, indent=4, sort_keys=True)
        print(json_str)

    else:

        for item in log_lists:
            show_logs(item['logs'], item['heading'])


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
