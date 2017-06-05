import struct
from functools import reduce

from utlz import flo


def create_signature_input(ee_cert, sct, *_, **__):
    # cf. https://tools.ietf.org/html/rfc6962#section-3.2

    signature_type = 0  # 0 means certificate_timestamp
    entry_type = 0  # 0: ASN.1Cert, 1: PreCert

    def reduce_func(accum_value, current):
        fmt = accum_value[0] + current[0]
        values = accum_value[1] + (current[1], )
        return fmt, values

    initializer = ('!', ())

    # fmt = '!BBQh...', values = [<sct.version>, <signature_type>, ...]
    fmt, values = reduce(reduce_func, [
        ('B', sct.version.val),
        ('B', signature_type),
        ('Q', sct.timestamp),
        ('h', entry_type),

        # signed_entry
        ('B', ee_cert.len1),
        ('B', ee_cert.len2),
        ('B', ee_cert.len3),
        (flo('{ee_cert.len}s'), ee_cert.der),

        ('h', sct.extensions_len),
    ], initializer)
    return struct.pack(fmt, *values)


def create_signature_input_precert(ee_cert, sct, issuer_cert):
    # cf. https://tools.ietf.org/html/rfc6962#section-3.2

    signature_type = 0  # 0 means certificate_timestamp
    entry_type = 1  # 0: ASN.1Cert, 1: PreCert

    tbscert = ee_cert.tbscert.without_ct_extensions

    def reduce_func(accum_value, current):
        fmt = accum_value[0] + current[0]
        values = accum_value[1] + (current[1], )
        return fmt, values

    initializer = ('!', ())

    # fmt = '!BBQh...', values = [<sct.version>, <signature_type>, ...]
    fmt, values = reduce(reduce_func, [
        ('B', sct.version.val),
        ('B', signature_type),
        ('Q', sct.timestamp),
        ('h', entry_type),

        # signed_entry

        # issuer_key_hash[32]
        ('32s', issuer_cert.pubkey_hash),

        # tbs_certificate (rfc6962, page 12)
        #  * DER encoded TBSCertificate of the ee_cert
        #    * without SCT extension
        ('B', tbscert.len1),
        ('B', tbscert.len2),
        ('B', tbscert.len3),
        (flo('{tbscert.len}s'), tbscert.der),

        ('h', sct.extensions_len),
    ], initializer)
    return struct.pack(fmt, *values)
