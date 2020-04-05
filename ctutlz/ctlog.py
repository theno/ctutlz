import json
import re
import urllib.request as urllib_request
from os.path import abspath, expanduser, join, isfile, dirname

import html2text
from utlz import load_json, namedtuple, text_with_newlines
from utlz.types import Enum

from ctutlz.utils.encoding import decode_from_b64, encode_to_b64
from ctutlz.utils.encoding import digest_from_b64
from ctutlz.utils.logger import logger

# https://groups.google.com/forum/#!topic/certificate-transparency/zZwGExvQeiE
# PENDING:
#       The Log has requested inclusion in the Log list distributor’s trusted Log list,
#       but has not yet been accepted.
#       A PENDING Log does not count as ‘currently qualified’, and does not count as ‘once qualified’.
# QUALIFIED:
#       The Log has been accepted by the Log list distributor, and added to the CT checking code
#       used by the Log list distributor.
#       A QUALIFIED Log counts as ‘currently qualified’.
# USABLE:
#       SCTs from the Log can be relied upon from the perspective of the Log list distributor.
#       A USABLE Log counts as ‘currently qualified’.
# FROZEN (READONLY in JSON-schema):
#       The Log is trusted by the Log list distributor, but is read-only, i.e. has stopped accepting
#       certificate submissions.
#       A FROZEN Log counts as ‘currently qualified’.
# RETIRED:
#       The Log was trusted by the Log list distributor up until a specific retirement timestamp.
#       A RETIRED Log counts as ‘once qualified’ if the SCT in question was issued before the retirement timestamp.
#       A RETIRED Log does not count as ‘currently qualified’.
# REJECTED:
#       The Log is not and will never be trusted by the Log list distributor.
#       A REJECTED Log does not count as ‘currently qualified’, and does not count as ‘once qualified’.
KnownCTStates = Enum(
    PENDING='pending',
    QUALIFIED='qualified',
    USABLE='usable',
    READONLY='readonly',    # frozen
    RETIRED='retired',
    REJECTED='rejected'
)

Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'key',     # base-64 encoded, type: str
        'log_id',
        'mmd',   # v1: maximum_merge_delay
        'url',

        # optional ones:
        'description=None',
        'dns=None',
        'temporal_interval=None',
        'log_type=None',
        'state=None',    # JSON-schema has: pending, qualified, usable, readonly, retired, rejected

        'operated_by=None',


        # TODO add real checks; interact with logs (-> ctlog.py):

        # True, False, or None
        'active=None',        # log accepts new entries
        # True, False, or None
        'alive=None',         # log answers
    ],
    lazy_vals={
        'key_der': lambda self: decode_from_b64(self.key),  # type: bytes
        'log_id_der': lambda self: digest_from_b64(self.key),   # type: bytes
        'pubkey': lambda self: '\n'.join([                  # type: str
                                          '-----BEGIN PUBLIC KEY-----',
                                          text_with_newlines(text=self.key,
                                                             line_length=64),
                                          '-----END PUBLIC KEY-----']),
        'scts_accepted_by_chrome':
            lambda self:
                None if self.state is None else
                True if next(iter(self.state)) in [KnownCTStates.USABLE,
                                                   KnownCTStates.QUALIFIED,
                                                   KnownCTStates.READONLY] else
                False,
    }
)


# plurale tantum constructor
def Logs(log_dicts):
    '''
    Arg log_dicts example:
        {
            "logs": [
                {
                    "description": "Google 'Argon2017' log",
                    "log_id": "+tTJfMSe4vishcXqXOoJ0CINu/TknGtQZi/4aPhrjCg=",
                    "key": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEVG18id3qnfC6X/RtYHo3TwIlvxz2b4WurxXfaW7t26maKZfymXYe5jNGHif0vnDdWde6z/7Qco6wVw+dN4liow==",
                    "url": "https://ct.googleapis.com/logs/argon2017/",
                    "mmd": 86400,
                    "state": {
                        "rejected": {
                            "timestamp": "2018-02-27T00:00:00Z"
                        }
                    },
                    "temporal_interval": {
                        "start_inclusive": "2017-01-01T00:00:00Z",
                        "end_exclusive": "2018-01-01T00:00:00Z"
                    },
                    "operated_by": {
                        "name": "Google",
                        "email": [
                            "google-ct-logs@googlegroups.com"
                        ],
                    }
                },
    '''
    for log in log_dicts:
        # Make sure the lazy vals don't exist
        log.pop('log_id_der', None)
        log.pop('pubkey', None)
        log.pop('scts_accepted_by_chrome', None)
    # Pythonic:
    logs_out = [Log(**kwargs) for kwargs in log_dicts]
    # Easy to debug:
    if False:
        logs_out = []
        for kwargs in log_dicts:
            log = Log(**kwargs)
            logs_out.append(log)
    return logs_out


def set_operator_names(logs_dict):
    '''
    Fold the logs listing by operator into list of logs.
    Append operator information to each log

    Arg log_dicts example:
        {
            "operators": [
                {
                    "name": "Google",
                    "email": [
                        "google-ct-logs@googlegroups.com"
                    ],
                    "logs": [
                        {
                            "description": "Google 'Argon2017' log",
                            "log_id": "+tTJfMSe4vishcXqXOoJ0CINu/TknGtQZi/4aPhrjCg=",
                            "key": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEVG18id3qnfC6X/RtYHo3TwIlvxz2b4WurxXfaW7t26maKZfymXYe5jNGHif0vnDdWde6z/7Qco6wVw+dN4liow==",
                            "url": "https://ct.googleapis.com/logs/argon2017/",
                            "mmd": 86400,
                            "state": {
                                "rejected": {
                                    "timestamp": "2018-02-27T00:00:00Z"
                                }
                            },
                            "temporal_interval": {
                                "start_inclusive": "2017-01-01T00:00:00Z",
                                "end_exclusive": "2018-01-01T00:00:00Z"
                            }
                        },
    '''
    logs_dict['logs'] = []
    for operator in logs_dict['operators']:
        operator_name = operator['name']
        operator_email = operator['email']
        for log in operator['logs']:
            log['operated_by'] = {
                'name': operator_name,
                'email': operator_email
            }
            logs_dict['logs'].append(log)
    del logs_dict['operators']


'''logs included in chrome browser'''
BASE_URL = 'https://www.gstatic.com/ct/log_list/v2/'
URL_LOG_LIST = BASE_URL + 'log_list.json'
URL_ALL_LOGS = BASE_URL + 'all_logs_list.json'


def download_log_list(url=URL_ALL_LOGS):
    '''Download json file with known logs accepted by chrome and return the
    logs as a list of `Log` items.

    Return: dict, the 'logs_dict'

    logs_dict example: {
      'logs: [
        {
          "description": "Google 'Aviator' log",
          "key": "MFkwE..."
          "url": "ct.googleapis.com/aviator/",
          "maximum_merge_delay": 86400,
          "operated_by": [0],
          "final_sth": {
            ...
          },
          "dns_api_endpoint": ...
        },
      ],
      'operators': [
        ...
      ]
    }
    '''
    response = urllib_request.urlopen(url)
    response_str = response.read()
    try:
        data = json.loads(response_str)
    except TypeError:
        # Python-3.x < 3.6
        data = json.loads(response_str.decode('utf-8'))
    return data


def read_log_list(filename):
    '''Read log list from file `filename` and return as logs_dict.

    Return: dict, the 'logs_dict'

    logs_dict example: {
      'logs: [
        {
          "description": "Google 'Aviator' log",
          "key": "MFkwE..."
          "url": "ct.googleapis.com/aviator/",
          "maximum_merge_delay": 86400,
          "operated_by": [0],
          "final_sth": {
            ...
          },
          "dns_api_endpoint": ...
        },
      ],
      'operators': [
        ...
      ]
    }
    '''
    filename = abspath(expanduser(filename))
    data = load_json(filename)
    return data


def get_log_list(list_name='really_all_logs.json'):
    '''Try to read log list from local file.  If file not exists download
    log list.

    Return: dict, the 'logs_dict'

    logs_dict example: {
      'logs: [
        {
          "description": "Google 'Aviator' log",
          "key": "MFkwE..."
          "url": "ct.googleapis.com/aviator/",
          "maximum_merge_delay": 86400,
          "operated_by": [0],
          "final_sth": {
            ...
          },
          "dns_api_endpoint": ...
        },
      ],
      'operators': [
        ...
      ]
    }
    '''
    thisdir = dirname(__file__)
    filename = join(thisdir, list_name)
    if isfile(filename):
        logs_dict = read_log_list(filename)
    else:
        logs_dict = download_log_list(''.join([BASE_URL, list_name]))
    return logs_dict


def _log_dict_from_log_text(log_text):
    '''
    Args:
        log_text example (str):
            """
            ct.googleapis.com/pilot

            Base64 Log ID: pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=
            Operator: Google
            Started: 2013-03-25
            HTTPS supported: yes

            Maximum Merge Delay: 24 hours
            Contact: google-ct-logs@googlegroups.com
            Chrome inclusion status: Included."""

    return example: {
        'url': 'ct.googleapis.com/pilot/',
        'id_b64_non_calculated': 'pLkJkLQYWBSHuxOizGdwCj'
                                 'w1mAT5G9+443fNDsgN3BA=',
        'operated_by': ['Google'],
        'started': '2013-03-25',
        'https_supported': 'yes',
        'maximum_merge_delay': 86400,
        'contact': 'google-ct-logs@googlegroups.com',
        'chrome_inclusion_status': 'Included.',
        'chrome_status': 'included',
        'description': None,
        'key': None,
    }
    '''
    res = re.match(r'''(?P<log_url>[^ \n]+)
                       (?P<key_vals>(:?[^:]+:.+[\n$])*)
                       (?P<notes>(.*[\n$])*)''',
                   log_text,
                   flags=re.M | re.X)
    res_dict = res.groupdict()

    log_dict = {
        # normalize: assure url ends with a '/'
        'url': res_dict['log_url'].rstrip('/') + '/',
    }

    notes = res_dict.get('notes', '').strip()
    if notes:
        notes = re.sub(r'\s+', ' ', notes)  # just a oneliner, no formattings
        log_dict['notes'] = notes

    key_vals = res_dict.get('key_vals', '')
    for line in key_vals.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            val = val.strip()
            key = key.strip().lower().replace(' ', '_')
            if key == 'mmd':
                key = 'maximum_merge_delay'
            if key == 'maximum_merge_delay':
                if val.endswith('hours'):
                    hours = val.split(' ')[0]
                    val = int(hours) * 3600
            if key == 'base64_log_id':
                key = 'id_b64_non_calculated'
            if key == 'operator':
                key = 'operated_by'
                val = [val]
            log_dict[key] = val

    for key in 'description', 'key', 'maximum_merge_delay':
        # set to default `None` if they not exist
        log_dict[key] = log_dict.get(key, None)

    return log_dict


def _text_from_html(html):
    h2t = html2text.HTML2Text()
    h2t.ignore_links = True
    return h2t.handle(html)


def _logs_dict_from_html(html):
    text = _text_from_html(html)  # Python-3

    # ged rid of ending section
    text = text.split('###  Known Logs')[-1]

    # FIXME not needed anymore after redesign of known-logs.html?
    try:
        # remove erroneous ####-headers
        text = re.sub(r'####\s*$', '', text, flags=re.M)
        text = re.sub(r'####\s+(?=.*: )', '', text, flags=re.M)
        # remove backticks (from surrounding log ids)
        text = re.sub(r'`', '', text, flags=re.M)
    except Exception:  # InvocationError:
        # Python-2.6
        # remove erroneous ####-headers
        text = re.sub(r'####\s*$', '', text)
        text = re.sub(r'####\s+(?=.*: )', '', text)
        # remove backticks (from surrounding log ids)
        # (does not work at Python-2.6: text = re.sub(r'`', '', text, re.M) )
        text = text.replace('`', '')

    # normalize spaces (for Python-2)
    text = text.replace('\xa0', ' ')
    # remove trailing spaces
    text = '\n'.join([line.rstrip() for line in text.split('\n')])

    text = text.split('\n\n---\n')[0]  # get rid of bottom comments section

    # logger.debug(text)

    # keep only text blocks with log lists, drop first section
    log_blocks = text.split('\n### ', -1)[1:]

    # logger.debug(log_blocks)

    logs_dict = {}
    for text_block in log_blocks:
        # eg. (' Active Logs', ' \n\n#### ct.googleapis.com/pilot\n...')
        name, rest = text_block.split('\n\n', 1)
        # title of the log block,  eg. title = 'included in chrome'
        title = name.strip().lower().replace(' ', '_')

        # FIXME: simplify. Currently only special-purpose-logs are listed on
        #        known-log.html
        chrome_state = None
        print("Title: '%s'" % title)
        if title.startswith('included'):
            chrome_state = ChromeStates.INCLUDED
        elif title.startswith('frozen'):
            chrome_state = ChromeStates.FROZEN
        elif title.startswith('pending'):
            chrome_state = ChromeStates.PENDING
        elif title.startswith('disqualified'):
            chrome_state = ChromeStates.DISQUALIFIED
        elif title.startswith('rejected'):
            chrome_state = ChromeStates.REJECTED
        elif 'distrusted' in title:
            chrome_state = ChromeStates.DISTRUSTED
        elif title.startswith('other'):
            chrome_state = None
        elif title.startswith('special_purpose_logs'):
            chrome_state = None
        elif title.startswith('test_logs'):
            chrome_state = ChromeStates.TEST
        else:
            raise Exception('unknown chrome_state "%s" for log-text_block' % title)

        logs_dict[title] = []
        for log_text in rest.strip().lstrip('#### ').split('\n\n#### '):
            if log_text.strip() != '':
                log_dict = _log_dict_from_log_text(log_text)
                log_dict['chrome_state'] = chrome_state

                logs_dict[title].append(log_dict)

    return logs_dict


def logs_dict_from_webpage():
    '''Download log-list webpage and return as logs_dict.'''
    url = 'https://www.certificate-transparency.org/known-logs'
    response = urllib_request.urlopen(url)
    html = response.read().decode('utf-8')
    return _logs_dict_from_html(html)


def print_schema():
    thisdir = dirname(__file__)
    filename = join(thisdir, 'log_list_schema.json')
    with open(filename, 'r') as fh:
        json_str = fh.read()
    # print(json_str.strip())
    print('TODO')