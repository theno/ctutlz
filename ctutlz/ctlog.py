from __future__ import unicode_literals  # for Python-2
import json
import re
try:
    # since python 3.6
    import urllib.request as urllib_request
except ImportError:
    import urllib as urllib_request
from os.path import abspath, expanduser, join, isfile, dirname

import html2text
from utlz import load_json, namedtuple, text_with_newlines
from utlz.types import Enum

from ctutlz.utils.encoding import decode_from_b64, encode_to_b64
from ctutlz.utils.encoding import digest_from_b64
from ctutlz.utils.logger import logger


# states 'compliant with chrome ct policy'
ChromeStates = Enum(INCLUDED='included',
                    FROZEN='frozen',

                    PENDING='pending for inclusion',

                    DISQUALIFIED='disqualified',
                    REJECTED='rejected',
                    DISTRUSTED='distrusted')

Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'description',
        'key',     # base-64 encoded, type: str
        'url',
        'maximum_merge_delay',
        'operated_by',

        # optional infos from *.json
        'final_sth=None',
        'disqualified_at=None',
        'dns_api_endpoint=None',

        # optional infos from webpage 'known logs'
        'contact=None',
        'chrome_bug=None',
        'notes=None',
        'id_b64_non_calculated=None',
        'certificate_expiry_range=None',

        # ChromeStates attribute or None
        'chrome_state=None',

        # TODO add real checks; interact with logs (-> ctlog.py):

        # True, False, or None
        'active=None',        # log accepts new entries
        # True, False, or None
        'alive=None',         # log answers
    ],
    lazy_vals={
        'key_der': lambda self: decode_from_b64(self.key),  # type: bytes
        'id_der': lambda self: digest_from_b64(self.key),   # type: bytes
        'id_b64': lambda self: encode_to_b64(self.id_der),  # type: str
        'pubkey': lambda self: '\n'.join([                  # type: str
                                          '-----BEGIN PUBLIC KEY-----',
                                          text_with_newlines(text=self.key,
                                                             line_length=64),
                                          '-----END PUBLIC KEY-----']),
        'scts_accepted_by_chrome':
            lambda self:
                None if self.chrome_state is None else
                True if self.chrome_state in [ChromeStates.INCLUDED,
                                              ChromeStates.FROZEN] else
                False,
    }
)


# plurale tantum constructor
def Logs(log_dicts):
    '''
    Arg log_dicts example: [
        {
            'description': ...,
            'key': ...,
            'url': ...,
            'maximum_merge_delay': ...,
            'operated_by': ...,

            'final_sth': ...,  # optional
            'disqualified_at=None': ...,
            'dns_api_endpoint=None': ...,

            # optional
            'started': ...,
            'submitted_for_inclusion_in_chrome': ...,
            'contact': ...,
            'chrome_bug'. ...,
            'notes': ...,
            'id_b64_non_calculated': ...,

            'chrome_state', CHROME_STATE.<enum>
        },
    ]
    '''
    for log in log_dicts:
        log.pop('id_b64', None)
        log.pop('pubkey', None)
        log.pop('scts_accepted_by_chrome', None)
    return [Log(**kwargs) for kwargs in log_dicts]


def set_operator_names(logs_dict):
    '''For each log in logs_dict overwrite the operator numbers by operator
    names.

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
    for log in logs_dict['logs']:
        operator_ids = log['operated_by']
        operator_names = [operator['name']
                          for operator
                          in logs_dict['operators']
                          if operator['id'] in operator_ids]
        log['operated_by'] = operator_names


def unset_operator_names(logs_dict):
    '''For each log in logs_dict reset the operator names by operator numbers.

    logs_dict example: {
      'logs: [
        {
          "description": "Google 'Aviator' log",
          "key": "MFkwE..."
          "url": "ct.googleapis.com/aviator/",
          "maximum_merge_delay": 86400,
          "operated_by": ["Google"],
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
    for log in logs_dict['logs']:
        operator_names = log['operated_by']

        operator_ids = [operator['id']
                        for operator
                        in logs_dict['operators']
                        if operator['name'] in operator_names]
        log['operated_by'] = operator_ids


'''logs included in chrome browser'''
BASE_URL = 'https://www.gstatic.com/ct/log_list/'
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
    try:
        text = _text_from_html(html)  # Python-3
    except UnicodeDecodeError:
        text = _text_from_html(html.decode('utf-8'))  # Python-2

    # ged rid of ending section
    text = text.split('To have another log included in this list')[0]
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

    logger.debug(text)

    # keep only text blocks with log lists, drop first and second section
    log_blocks = text.split('\n### ', -1)[2:]

    logs_dict = {}
    for text_block in log_blocks:
        # eg. (' Active Logs', ' \n\n#### ct.googleapis.com/pilot\n...')
        name, rest = text_block.split('\n\n', 1)
        # title of the log block,  eg. title = 'included in chrome'
        title = name.strip().lower().replace(' ', '_')

        chrome_state = None
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
        else:
            raise Exception('unknown chrome_state for log-text_block')

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
