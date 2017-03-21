import collections
import os
from tempfile import NamedTemporaryFile as tempfile

from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from OpenSSL.crypto import verify, X509, PKey, Error as OpenSSL_crypto_Error
from utlz import flo

from ctutlz.utils.cmd import run_cmd, CmdResult


SctValidationResult = collections.namedtuple(
    typename='SctValidationResult',
    field_names=[
        'ee_cert',   # DER format
        'sct',       # type: Sct
        'log',       # type: Log
        'verified',  # True or False
        'output',    # type: str
        'cmd_res',   # CmdResult (for debugging) # FIXME remove
    ]
)


def find_log(sct, logs):
    for log in logs:
        if log.id_der == sct.log_id:
            return log
    return None


def verify_signature_CLUNKY(signature_input, signature, pubkey):
    # with-cascade required for python2.6 support
    with tempfile() as signature_input_file:
        with tempfile() as signature_file:
            with tempfile() as pubkey_file:

                signature_input_file.write(signature_input)
                signature_input_file.seek(0)

                signature_file.write(signature)
                signature_file.seek(0)

                pubkey_file.write(pubkey)
                pubkey_file.seek(0)

                openssl = os.environ.get('OPENSSL_CMD', 'openssl')
                cmd = flo('{openssl}  dgst -sha256 -verify {pubkey_file.name} '
                          '-signature {signature_file.name} '
                          '{signature_input_file.name}')
                res = run_cmd(cmd, timeout=30, max_try=3)
                output = res.stdout_str + res.stderr_str
                if res.exitcode == 0:
                    return True, output, res
                return False, output, res


def verify_signature(signature_input, signature, pubkey):
    cryptography_key = serialization.load_pem_public_key(pubkey, backend)

    pkey = PKey.from_cryptography_key(cryptography_key)

    auxiliary_cert = X509()
    auxiliary_cert.set_pubkey(pkey)

    try:
        verify(cert=auxiliary_cert,
               signature=signature,
               data=signature_input,
               digest='sha256')
    except OpenSSL_crypto_Error:
        cmd_res = CmdResult(1, None, None, None, None)
        return False, 'Verification Failure\n', cmd_res

    cmd_res = CmdResult(0, None, None, None, None)
    return True, 'Verified OK\n', cmd_res


def verify_sct(ee_cert, sct, logs, issuer_cert, sign_input_func):
    log = find_log(sct, logs)
    if log:
        verified, output, cmd_res = verify_signature(
            signature_input=sign_input_func(ee_cert, sct, issuer_cert),
            signature=sct.signature,
            pubkey=log.pubkey.encode('ascii')
        )
        return SctValidationResult(ee_cert, sct, log,
                                   verified, output, cmd_res)
    return SctValidationResult(ee_cert, sct, log,
                               verified=False, output='', cmd_res=None)


def verify_scts(ee_cert, scts, logs, issuer_cert, sign_input_func):
    if scts:
        return [verify_sct(ee_cert, sct, logs, issuer_cert, sign_input_func)
                for sct
                in scts]
    return []
