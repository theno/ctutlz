import json
try:
    # since python 3.6
    import urllib.request as urllib_request
except ImportError:
    import urllib as urllib_request
from os.path import join, isfile, dirname

from utlz import namedtuple, text_with_newlines, load_json

from ctutlz.utils import decode_from_pem, digest_from_pem
from ctutlz.utils import digest_from_pem_encoded_to_pem


Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'description',
        'key',     # PEM encoded, type: str
        'url',
        'maximum_merge_delay',
        'operated_by',
    ],
    lazy_vals={
        'key_der': lambda self: decode_from_pem(self.key),         # type: bytes
        'id_der': lambda self: digest_from_pem(self.key),          # type: bytes
        'id_pem': lambda self: digest_from_pem_encoded_to_pem(self.key),  # str
        'pubkey': lambda self: '\n'.join(['-----BEGIN PUBLIC KEY-----',   # str
                                          text_with_newlines(text=self.key,
                                                             line_length=64),
                                          '-----END PUBLIC KEY-----']),
    }
)


def Logs(log_dicts):
    return [Log(**kwargs) for kwargs in log_dicts]


def logs_with_operator_names(logs_dict):
    for log in logs_dict['logs']:
        operator_ids = log['operated_by']
        operator_names = [operator['name']
                          for operator
                          in logs_dict['operators']
                          if operator['id'] in operator_ids]
        log['operated_by'] = operator_names
    return Logs(logs_dict['logs'])


def download_log_list_accepted_by_chrome():
    '''Download json file with known logs accepted by chrome and return the
    logs as a list of `Log` items.
    '''
    url = 'https://www.certificate-transparency.org/known-logs/log_list.json'
    response = urllib_request.urlopen(url)
    response_str = response.read()
    try:
        data = json.loads(response_str)
    except TypeError:
        # python 3.x < 3.6
        data = json.loads(response_str.decode('utf-8'))
    return logs_with_operator_names(data)


def get_log_list():
    try:
        return get_log_list.logs  # singleton function attribute
    except AttributeError:
        filename = join(dirname(dirname(__file__)), 'log_list.json')
        if isfile(filename):
            data = load_json(filename)
            get_log_list.logs = logs_with_operator_names(data)
        else:
            get_log_list.logs = download_log_list_accepted_by_chrome()
    return get_log_list.logs
