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


# a subset of this states is 'compliant with chrome ct policy': INCLUDED, FROZEN
ChromeStates = Enum(INCLUDED='included',
                    FROZEN='frozen',

                    PENDING='pending for inclusion',

                    DISQUALIFIED='included, but then disqualified',

                    NOT_QUALIFIED='applied for inclusion but did not qualify',
                    NOT_INCLUDED='not included')

Functions = Enum(ACTIVE='active',
                 FROZEN='frozen',
                 SPECIAL_PURPOSE='special purpose',
                 CEASED='ceased operation')

Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'description',
        'key',     # base-64 encoded, type: str
        'url',
        'maximum_merge_delay',
        'operated_by',

        'final_sth=None',
        'disqualified_at=None',
        'dns_api_endpoint=None',

        'started=None',
        'submitted_for_inclusion_in_chrome=None',
        'contact=None',
        'https_supported=None',
        'chrome_inclusion_status=None',
        'notes=None',
        'id_b64_non_calculated=None',

        # ChromeStates attribute or None
        'chrome_status=None',
        # Functions attribute or None
        'function=None',  # included, pending for inclusion, testing, ...

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
        'compliant_to_chrome_ct_policy':
            lambda self:
                None if self.chrome_status is None else
                True if self.chrome_status in [ChromeStates.INCLUDED,
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
            'https_supported': ...,
            'chrome_inclusion_status': ...,
            'notes': ...,
            'id_b64_non_calculated': ...,
            'compliant_to_chrome_ct_policy': ...,
        }
    ],
    ]
    '''
    return [Log(**kwargs) for kwargs in log_dicts]


def amend_by_chrome_inclusion_status(logs_dict):
    '''Amend (mutable) each log of dict `logs_dict` by its inclusion status.

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
        if 'final_sth' in log.keys():
            log['chrome_inclusion_status'] = 'Frozen'
        else:
            log['chrome_inclusion_status'] = 'Included'


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
    '''
    filename = abspath(expanduser(filename))
    data = load_json(filename)
    return data


def get_log_list(list_name='all_logs_list.json'):
    '''Try to read log list from local file.  If file not exists download
    log list.

    Return: dict, the 'logs_dict'
    '''
    thisdir = dirname(__file__)
    filename = join(thisdir, list_name)
    if isfile(filename):
        logs_dict = read_log_list(filename)
    else:
        logs_dict = download_log_list(''.join([BASE_URL, list_name]))
    return logs_dict


def _log_dict_from_log_text(log_text):
    res = re.match(r'''(?P<url>[^ \n]+)              # log url
                       (?P<ignore>\s[-]\s)?          # optional ' - ' (ignore)
                       (?P<notes_head>[^\n]*\n?)     # notes headline
                       (?P<notes_text>(:?[^:]+\n)*)  # notes text
                       (?P<rest>(:?.*[\n$])*)''',
                   log_text,
                   flags=re.M|re.X)
    res_dict = res.groupdict()
    log_dict = {
        # normalize: assure trailing '/'
        'url': res_dict['url'].rstrip('/') + '/',
    }
    notes_head = res_dict.get('notes_head', '').strip()
    if notes_head:
        notes_text = res_dict.get('notes_text', '').strip()
        notes = ' '.join([notes_head, notes_text])
        notes = re.sub(r'\s+', ' ', notes)
        log_dict['notes'] = notes

    key_vals = res_dict.get('rest', '')
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

    cis = log_dict.get('chrome_inclusion_status', False)
    if cis:
        # disqualified-case must be before included-case
        if 'disqualified' in cis.lower():
            log_dict['chrome_status'] = ChromeStates.DISQUALIFIED
        elif cis.lower().startswith('included'):
            log_dict['chrome_status'] = ChromeStates.INCLUDED
        elif cis.lower().startswith('pending'):
            log_dict['chrome_status'] = ChromeStates.PENDING
        elif cis.lower().startswith('Applied for inclusion but did '
                                  'not qualify'):
            log_dict['chrome_status'] = ChromeStates.NOT_QUALIFIED
        elif cis.lower().startswith('frozen'):
            log_dict['chrome_status'] = ChromeStates.FROZEN
        elif cis.lower().startswith('not included'):
            log_dict['chrome_status'] = ChromeStates.NOT_INCLUDED

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
        text = re.sub(r'####\s+(?=.*:)', '', text, flags=re.M)
        # remove backticks (from surrounding log ids)
        text = re.sub(r'`', '', text, flags=re.M)
    except Exception:  # InvocationError:
        # Python-2.6
        # remove erroneous ####-headers
        text = re.sub(r'####\s*$', '', text)
        text = re.sub(r'####\s+(?=.*:)', '', text)
        # remove backticks (from surrounding log ids)
        # (does not work at Python-2.6: text = re.sub(r'`', '', text, re.M) )
        text = text.replace('`', '')

    # normalize spaces (for Python-2)
    text = text.replace('\xa0', ' ')
    # remove trailing spaces
    text = '\n'.join([line.rstrip() for line in text.split('\n')])

    # keep only text blocks with log lists, drop first and second section
    log_blocks = text.split('\n### ', -1)[2:]

    logs_dict = {}
    for text_block in log_blocks:
        # eg. (' Active Logs', ' \n\n#### ct.googleapis.com/pilot\n...')
        name, rest = text_block.split('\n\n', 1)
        # eg. log_list_name = 'active_logs'
        log_list_name = name.strip().lower().replace(' ', '_')
        logs_dict[log_list_name] = []
        for log_text in rest.strip().lstrip('#### ').split('\n\n#### '):
            if log_text.strip() != '':
                log_dict = _log_dict_from_log_text(log_text)

                if log_list_name == 'active_logs':
                    log_dict['function'] = Functions.ACTIVE
                elif log_list_name == 'frozen_logs':
                    log_dict['function'] = Functions.FROZEN
                elif log_list_name == 'special_purpose_logs':
                    log_dict['function'] = Functions.SPECIAL_PURPOSE
                elif log_list_name == 'logs_that_ceased_operation':
                    log_dict['function'] = Functions.CEASED

                logs_dict[log_list_name].append(log_dict)

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
