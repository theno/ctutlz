import struct
from functools import reduce

from utlz import flo


def create_signature_input(ee_cert, sct, *_, **__):
    # cf. https://tools.ietf.org/html/rfc6962#section-3.2

    signature_type = 0
    entry_type = 0  # 0: ASN.1Cert, 1: PreCert

    def reduce_func(accum_value, current):
        fmt = accum_value[0] + current[0]
        values = accum_value[1] + (current[1], )
        return fmt, values

    initializer = ('!', ())

    fmt, values = reduce(reduce_func, [
        ('B', sct.version),
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

    signature_type = 0
    entry_type = 1  # 0: ASN.1Cert, 1: PreCert

    tbscert_der = ee_cert.tbscert_without_sctlist_der
    tbscert_len = ee_cert.tbscert_without_sctlist_len
    tbscert_len1 = ee_cert.tbscert_without_sctlist_len1
    tbscert_len2 = ee_cert.tbscert_without_sctlist_len2
    tbscert_len3 = ee_cert.tbscert_without_sctlist_len3

    def reduce_func(accum_value, current):
        fmt = accum_value[0] + current[0]
        values = accum_value[1] + (current[1], )
        return fmt, values

    initializer = ('!', ())

    fmt, values = reduce(reduce_func, [
        ('B', sct.version),
        ('B', signature_type),
        ('Q', sct.timestamp),
        ('h', entry_type),

        # signed_entry

        # issuer_key_hash[32]
        ('32s', issuer_cert.pubkey_hash),

        # tbs_certificate (rfc6962, page 12)
        #  * DER encoded TBSCertificate of the ee_cert
        #    * without SCT extension
        ('B', tbscert_len1),
        ('B', tbscert_len2),
        ('B', tbscert_len3),
        (flo('{tbscert_len}s'), tbscert_der),

        ('h', sct.extensions_len),
    ], initializer)
    return struct.pack(fmt, *values)
