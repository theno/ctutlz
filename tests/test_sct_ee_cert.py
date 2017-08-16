from os.path import join, dirname

import OpenSSL
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.type.univ import ObjectIdentifier, Sequence
from utlz import flo

from ctutlz.sct.ee_cert import pyopenssl_certificate_from_der, EndEntityCert


def test_pyopenssl_certificate_from_der():
    basedir = join(dirname(__file__), 'data', 'test_sct_ee_cert')

    for filename in ['ev_cert.der', 'cert_no_ev.der']:
        cert_der = open(flo('{basedir}/{filename}'), 'rb').read()
        got = pyopenssl_certificate_from_der(cert_der)

        assert type(got) is OpenSSL.crypto.X509


def test_is_ev_cert():
    basedir = join(dirname(__file__), 'data', 'test_sct_ee_cert')

    test_data = [
        ('ev_cert.der', True),
        ('cert_no_ev.der', False),
    ]

    for filename, expected in test_data:
        cert_der = open(flo('{basedir}/{filename}'), 'rb').read()
        ee_cert = EndEntityCert(cert_der)

        assert ee_cert.is_ev_cert is expected
