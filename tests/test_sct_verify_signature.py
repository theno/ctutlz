from os.path import join, dirname

from utlz import flo

from ctutlz.sct.verification import verify_signature


def test_verify_signature():
    basedir = join(dirname(__file__), 'data', 'test_sct_verify_signature')

    signature_input = \
        open(flo('{basedir}/signature_input_valid.bin'), 'rb').read()
    signature = open(flo('{basedir}/signature.der'), 'rb').read()
    pubkey = open(flo('{basedir}/pubkey.pem'), 'rb').read()

    got_verified, got_output, got_cmd_res = \
        verify_signature(signature_input, signature, pubkey)

    assert got_verified is True
    assert got_output == 'Verified OK\n'
    assert got_cmd_res.exitcode == 0

    signature_input = b'some invalid signature input'

    got_verified, got_output, got_cmd_res = \
        verify_signature(signature_input, signature, pubkey)

    assert got_verified is False
    assert got_output == 'Verification Failure\n'
    assert got_cmd_res.exitcode == 1
