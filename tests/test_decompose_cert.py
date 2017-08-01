from os.path import abspath, dirname, join

import pyasn1_modules
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.codec.der.encoder import encode as der_encoder

from ctutlz.scripts.decompose_cert import cert_der_from_data


def test_cert_der_from_data():
    thisdir = abspath(dirname(__file__))
    testdata = join(thisdir, 'data', 'test_decompose_cert')

    with open(join(testdata, 'cert.der'), 'rb') as fh:
        cert_der = fh.read()
    with open(join(testdata, 'cert.b64'), 'rb') as fh:
        cert_b64 = fh.read()
    with open(join(testdata, 'cert.pem'), 'rb') as fh:
        cert_pem = fh.read()

    assert cert_der_from_data(cert_der) == cert_der
    assert cert_der_from_data(cert_b64) == cert_der
    assert cert_der_from_data(cert_pem) == cert_der


def test_parse_cert_with_pyasn1():
    thisdir = abspath(dirname(__file__))
    testdata = join(thisdir, 'data', 'test_decompose_cert')

    with open(join(testdata, 'cert.der'), 'rb') as fh:
        cert_der = fh.read()

    cert, _ = der_decoder(cert_der,
                          asn1Spec=pyasn1_modules.rfc5280.Certificate())
    assert type(cert) is pyasn1_modules.rfc5280.Certificate

    re_encoded = der_encoder(cert)
    assert type(re_encoded) is bytes
    assert cert_der == re_encoded
