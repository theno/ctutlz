import collections
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from OpenSSL.crypto import verify, X509, PKey, Error as OpenSSL_crypto_Error

from ctutlz.utils.cmd import CmdResult


SctVerificationResult = collections.namedtuple(
    typename='SctVerificationResult',
    field_names=[
        'ee_cert',   # DER format
        'sct',       # type: Sct
        'log',       # type: Log
        'verified',  # True or False
        'output',    # type: str  # FIXME remove
        'cmd_res',   # CmdResult (for debugging) # FIXME remove
    ]
)


def find_log(sct, logs):
    for log in logs:
        if log.id_der == sct.log_id.tdf:
            return log
    return None


def verify_signature(signature_input, signature, pubkey_pem):
    cryptography_key = serialization.load_pem_public_key(pubkey_pem, backend)

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
            pubkey_pem=log.pubkey.encode('ascii')
        )
        return SctVerificationResult(ee_cert, sct, log,
                                     verified, output, cmd_res)
    return SctVerificationResult(ee_cert, sct, log,
                                 verified=False, output='', cmd_res=None)


def verify_scts(ee_cert, scts, logs, issuer_cert, sign_input_func):
    if scts:
        return [verify_sct(ee_cert, sct, logs, issuer_cert, sign_input_func)
                for sct
                in scts]
    return []
