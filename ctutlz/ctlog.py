import json
import re
import requests
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

        'operated_by=None'
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
    logs_out = []
    for log in log_dicts:
        logs_out += [Log(**kwargs) for kwargs in log['logs']]

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
BASE_URL = 'https://www.gstatic.com/ct/log_list/v3/'
URL_LOG_LIST = BASE_URL + 'log_list.json'
URL_ALL_LOGS = BASE_URL + 'all_logs_list.json'


def download_log_list(url=URL_ALL_LOGS):
    '''Download json file with known logs accepted by chrome and return the
    logs as a list of `Log` items.

    Return: dict, the 'logs_dict'

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
    response = requests.get(url)
    response_str = response.text
    data = json.loads(response_str)
    data['url'] = url

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


def print_schema():
    thisdir = dirname(__file__)
    filename = join(thisdir, 'log_list_schema.json')
    with open(filename, 'r') as fh:
        json_str = fh.read()
    # print(json_str.strip())
    print('TODO')
