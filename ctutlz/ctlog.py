import json
try:
    # since python 3.6
    import urllib.request as urllib_request
except ImportError:
    import urllib as urllib_request
from os.path import abspath, expanduser, join, isfile, dirname

from utlz import load_json, namedtuple, text_with_newlines

from ctutlz.utils.encoding import decode_from_b64, encode_to_b64
from ctutlz.utils.encoding import digest_from_b64, sha256_digest


Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'description',
        'key',     # base-64 encoded, type: str
        'url',
        'maximum_merge_delay',
        'operated_by',
    ],
    lazy_vals={
        'key_der': lambda self: decode_from_b64(self.key),  # type: bytes
        'id_der': lambda self: digest_from_b64(self.key),   # type: bytes
        'id_b64': lambda self: encode_to_b64(self.id_der),  # type: str
        'pubkey': lambda self: '\n'.join([                  # type: str
                              '-----BEGIN PUBLIC KEY-----',
                              text_with_newlines(text=self.key, line_length=64),
                              '-----END PUBLIC KEY-----'
        ]),
        'pubkey_hash': lambda self: sha256_digest(self.key_der),  # TODO DEVEL
    }
)


# plurale tantum constructor
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


def download_log_list():
    '''Download json file with known logs accepted by chrome and return the
    logs as a list of `Log` items.
    '''
    url = 'https://www.certificate-transparency.org/known-logs/' \
          'all_logs_list.json'
    response = urllib_request.urlopen(url)
    response_str = response.read()
    try:
        data = json.loads(response_str)
    except TypeError:
        # python 3.x < 3.6
        data = json.loads(response_str.decode('utf-8'))
    return logs_with_operator_names(data)


def get_log_list():
    thisdir = dirname(__file__)
    filename = join(thisdir, 'all_logs_list.json')
    if isfile(filename):
        data = load_json(filename)
        logs = logs_with_operator_names(data)
    else:
        logs = download_log_list()
    for log in logs:
        assert log.id_der == digest_from_b64(log.key)
    return logs


def read_log_list(filename):
    filename = abspath(expanduser(filename))
    data = load_json(filename)
    return logs_with_operator_names(data)
