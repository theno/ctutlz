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
from ctutlz.ctlog import URL_LOG_LIST, URL_ALL_LOGS, Log, Logs, ChromeStates
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
    '''Merge two log lists `list_a` and `list_b` merged by log url.'''
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


def merge_log_lists(included_from_webpage,
                    frozen_from_webpage,
                    pending_from_webpage,
                    disqualified_from_webpage,
                    rejected_from_webpage,
                    distrusted_from_webpage,
                    other_from_webpage,
                    all_from_webpage,
                    log_list_logs, all_logs, **_):
    '''Merge log lists, warn on log list errors and return merged logs.'''
    # log lists

    # log_list.json contains defines the logs which are chrome ct policy
    # compliant
    #
    # 'll_...' means:     log is listed in log_list.json
    # 'nn_...' means: log is not listed in log_list.json

    ll_included = []
    ll_frozen = []
    ll_pending = []
    ll_disqualified = []
    ll_rejected = []
    ll_distrusted = []
    ll_other = []

    nn_included = []
    nn_frozen = []
    nn_pending = []
    nn_disqualified = []
    nn_rejected = []
    nn_distrusted = []
    nn_other = []

    # merge log_list.json with log lists from webpage

    ll_rest = log_list_logs

    ll_included, ll_rest, nn_included = \
        merge_log_list_r(ll_rest, included_from_webpage)
    ll_frozen, ll_rest, nn_frozen = \
        merge_log_list_r(ll_rest, frozen_from_webpage)
    ll_pending, ll_rest, nn_pending = \
        merge_log_list_r(ll_rest, pending_from_webpage)
    ll_disqualified, ll_rest, nn_rejected = \
        merge_log_list_r(ll_rest, disqualified_from_webpage)
    ll_rejected, ll_rest, nn_rejected = \
        merge_log_list_r(ll_rest, rejected_from_webpage)
    ll_distrusted, ll_rest, nn_distrusted = \
        merge_log_list_r(ll_rest, distrusted_from_webpage)
    ll_other, ll_rest, nn_other = \
        merge_log_list_r(ll_rest, other_from_webpage)

    # `ll_rest` now contains all logs from log_list.json which are not
    # listed on webpage (this list should be empty, else the webpage is missing
    # entries)

    # merge log lists with all_logs.json

    all_rest = all_logs  # logs listed in all_logs.json

    ll_included, all_rest = \
        merge_enrich_a_with_b(ll_included, all_rest)
    ll_frozen, all_rest = \
        merge_enrich_a_with_b(ll_frozen, all_rest)
    ll_pending, all_rest = \
        merge_enrich_a_with_b(ll_pending, all_rest)
    ll_disqualified, all_rest = \
        merge_enrich_a_with_b(ll_disqualified, all_rest)
    ll_rejected, all_rest = \
        merge_enrich_a_with_b(ll_rejected, all_rest)
    ll_distrusted, all_rest = \
        merge_enrich_a_with_b(ll_distrusted, all_rest)
    ll_other, all_rest = \
        merge_enrich_a_with_b(ll_other, all_rest)

    nn_included, all_rest = \
        merge_overwrite_a_with_b(nn_included, all_rest)
    nn_frozen, all_rest = \
        merge_overwrite_a_with_b(nn_frozen, all_rest)
    nn_pending, all_rest = \
        merge_overwrite_a_with_b(nn_pending, all_rest)
    nn_disqualified, all_rest = \
        merge_overwrite_a_with_b(nn_disqualified, all_rest)
    nn_rejected, all_rest = \
        merge_overwrite_a_with_b(nn_rejected, all_rest)
    nn_distrusted, all_rest = \
        merge_overwrite_a_with_b(nn_distrusted, all_rest)
    nn_other, all_rest = \
        merge_overwrite_a_with_b(nn_other, all_rest)

    # warn for missing logs on webpage

    for log in ll_rest:
        logger.warn(red(flo(
            'log in log_list.json not listet on webpage: {log.url}')))

    for log in all_rest:
        logger.warn(red(flo(
            'log in all_logs.json not listed on webpage: {log.url}')))

    # warn for wrongly listed logs

    for log in ll_pending:
        logger.warn(red(flo(
            'log pending for inclusion listed in log_list.json: {log.url}')))

    for log in ll_rejected:
        logger.warn(red(flo(
            'rejeted log listet in log_list.json: {log.url}')))

    for log in ll_distrusted:
        logger.warn(red(flo(
            'distrusted log listet in log_list.json: {log.url}')))

    for log in ll_other:
        logger.warn(red(flo(
            'other purpose log listet in log_list.json: {log.url}')))

    for log in nn_included:
        logger.warn(red(flo(
            'chrome included log not listet in log_list.json: {log.url}')))

    for log in nn_frozen:
        logger.warn(red(flo(
            'chrome frozen log not listet in log_list.json: {log.url}')))

    ll_rest, all_rest = \
        merge_enrich_a_with_b(ll_rest, all_rest)
    rest = ll_rest + all_rest

    # warn for logs only listed on webpage

    _, webpage_rest, _ = merge_log_list_r(all_from_webpage, log_list_logs)
    _, webpage_rest, _ = merge_log_list_r(all_from_webpage, all_logs)
    for log in webpage_rest:
        logger.warn(red(flo(
            'log not listet in log_list.json nor all_logs.json: {log.url}')))

    return [
        {'heading': 'included logs (log_list.json, webpage)',
         'logs': ll_included},
        {'heading': 'frozen logs (log_list.json, webpage)',
         'logs': ll_frozen},
        {'heading': 'pending logs (log_list.json, webpage)',
         'logs': ll_pending},
        {'heading': 'disqualified logs (log_list.json, webpage)',
         'logs': ll_disqualified},
        {'heading': 'rejected logs (log_list.json, webpage)',
         'logs': ll_rejected},
        {'heading': 'distrusted logs (log_list.json, webpage)',
         'logs': ll_distrusted},

        {'heading': 'included logs NOT IN log_list.json '
                    '(webpage, all_logs.json)',
         'logs': nn_included},
        {'heading': 'frozen logs NOT IN log_list.json (webpage, all_logs.json)',
         'logs': nn_frozen},
        {'heading': 'pending logs (webpage, all_logs.json)',
         'logs': nn_pending},
        {'heading': nn_disqualified,
         'logs': nn_disqualified},
        {'heading': 'rejected logs (webpage, all_logs.json)',
         'logs': nn_rejected},
        {'heading': 'distrusted logs (webpage, all_logs.json)',
         'logs': nn_distrusted},
        {'heading': 'other logs (webpage, all_logs.json)',
         'logs': nn_other},

        {'heading': 'UNLISTED ON WEBPAGE (log_list.json or all_logs.json)',
         'logs': rest},
    ]


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
        logger.verbose('Created with [ctloglist]'
                       '(https://github.com/theno/ctutlz#ctloglist)\n')
        logger.verbose('Merged log lists:')
        logger.verbose("* webpage [known logs]"
                       '(https://www.certificate-transparency.org/known-logs)')
        logger.verbose('* [log_list.json]'
                       '(https://www.gstatic.com/ct/log_list/log_list.json)')
        logger.verbose('* [all_logs_list.json]('
                       'https://www.gstatic.com/ct/log_list/all_logs_list.json)'
                       '\n')
        logger.info(flo('Version (Date): {today}\n'))
        logger.verbose(flo('Datetime: {now}\n'))
        logger.info('')  # formatting: insert empty line

    # from webpage

    webpage_dict = logs_dict_from_webpage()

    all_from_webpage = Logs([log_dict
                             for log_list
                             in [webpage_dict[key] for key in webpage_dict]
                             for log_dict
                             in log_list])

    included_from_webpage = Logs(webpage_dict['included_in_chrome'])
    webpage_dict.pop('included_in_chrome')

    frozen_from_webpage = Logs(webpage_dict['frozen_logs'])
    webpage_dict.pop('frozen_logs')

    pending_from_webpage = Logs(webpage_dict['pending_inclusion_in_chrome'])
    webpage_dict.pop('pending_inclusion_in_chrome')

    disqualified_from_webpage = \
        Logs(webpage_dict['disqualified_from_chrome'])
    webpage_dict.pop('disqualified_from_chrome')

    rejected_from_webpage = Logs(webpage_dict['rejected_by_chrome'])
    webpage_dict.pop('rejected_by_chrome')

    distrusted_from_webpage = Logs(webpage_dict[
        'completely_distrusted_by_chrome'])
    webpage_dict.pop('completely_distrusted_by_chrome')

    other_from_webpage = Logs(webpage_dict['other_logs'])
    webpage_dict.pop('other_logs')

    unknown_log_titles = [key for key in webpage_dict.keys()]
    if unknown_log_titles:
        logger.error(red(flo(
            'unknown log titles (i.e. log states): {unknown_log_titles}')))

    # log_list.json: chrome ct policy compliant logs

    log_list_dict = download_log_list(URL_LOG_LIST)
    set_operator_names(log_list_dict)
    for log_dict in log_list_dict['logs']:
        if 'disqualified_at' in log_dict.keys():
            log_dict['chrome_state'] = ChromeStates.DISQUALIFIED

    log_list_logs = Logs(log_list_dict['logs'])

    # all_logs_list.json

    all_dict = download_log_list(URL_ALL_LOGS)
    set_operator_names(all_dict)

    all_logs = Logs(all_dict['logs'])

    # merge lists and show the result

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
