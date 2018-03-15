from collections import namedtuple
from os.path import join, dirname

from utlz import flo

from ctutlz.sct.verification import verify_signature


Item = namedtuple(
    typename='TestItem',
    field_names=[
        'domain',
        'pubkey_pem',
        'signature_der',
        'signature_input_bin',
        'expected_verify',
    ])


def from_file(filename):
    basedir = join(dirname(__file__), 'data', 'test_sct_verify_signature')
    with open(flo('{basedir}/{filename}'), 'rb') as fh:
        data = fh.read()
    return data


def test_verify_signature():
    test_data = [
        Item(
            domain='',
            expected_verify=True,
            signature_input_bin=from_file('signature_input_valid.bin'),
            signature_der=from_file('signature.der'),
            pubkey_pem=from_file('pubkey.pem')
        ),
        Item(
            domain='',
            expected_verify=False,
            signature_input_bin=b'some invalid signature input',
            signature_der=from_file('signature.der'),
            pubkey_pem=from_file('pubkey.pem')
        ),
        Item(
            domain='google.com',
            expected_verify=True,
            signature_input_bin=from_file('google.com/signature_input.bin'),
            signature_der=from_file('google.com/signature.der'),
            pubkey_pem=from_file('google.com/pubkey.pem')
        ),
        # Item(
        #     domain='pirelli.com',
        #     expected_verify=True,
        #     signature_input_bin=from_file('pirelli.com/signature_input.bin'),
        #     signature_der=from_file('pirelli.com/signature.der'),
        #     pubkey_pem=from_file('pirelli.com/pubkey.pem')
        # ),
    ]
    for item in test_data:
        assert verify_signature(item.signature_input_bin,
                                item.signature_der,
                                item.pubkey_pem) \
            is item.expected_verify, flo('verify_signature() for {item.domain} '
                                         'must return {item.expected_verify}')
