from os.path import join, dirname

from utlz import flo

from ctutlz.sct.verification import verify_signature


def test_verify_signature():
    basedir = join(dirname(__file__), 'data', 'test_sct_verify_signature')

    signature_input = \
        open(flo('{basedir}/signature_input_valid.bin'), 'rb').read()
    signature = open(flo('{basedir}/signature.der'), 'rb').read()
    pubkey = open(flo('{basedir}/pubkey.pem'), 'rb').read()

    assert verify_signature(signature_input, signature, pubkey) is True

    signature_input = b'some invalid signature input'

    assert verify_signature(signature_input, signature, pubkey) is False
