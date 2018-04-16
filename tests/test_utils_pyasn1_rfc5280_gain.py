import os.path

from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1_modules import rfc5280

from ctutlz.utils.pyasn1_rfc5280_gain import RelativeDistinguishedName, Name


def test_RelativeDistinguishedName():
    thisdir = os.path.dirname(__file__)
    with open(os.path.join(thisdir,
                           'data',
                           'test_pyasn1_rfc2580_gain',
                           'webmail.gov.ab.ca.der'),
              'rb') as fh:
        cert_der = fh.read()

    cert_pyasn1, __ = der_decoder(cert_der, rfc5280.Certificate())
    tbscert = cert_pyasn1.getComponentByName('tbsCertificate')
    issuer = tbscert['issuer']
    rdns = issuer['rdnSequence']
    rdn = rdns[0]
    rdn = RelativeDistinguishedName(rdn)
    assert rdn.type == '2.5.4.6'
    assert rdn.type_str == 'C'
    assert rdn.value == 'US'
    assert rdn.str == 'C=US'
    assert str(rdn) == 'C=US'


def test_Name():
    thisdir = os.path.dirname(__file__)
    with open(os.path.join(thisdir,
                           'data',
                           'test_pyasn1_rfc2580_gain',
                           'webmail.gov.ab.ca.der'),
              'rb') as fh:
        cert_der = fh.read()

    cert_pyasn1, __ = der_decoder(cert_der, rfc5280.Certificate())
    tbscert = cert_pyasn1.getComponentByName('tbsCertificate')
    issuer = tbscert['issuer']
    issuer = Name(issuer)

    assert str(issuer) == 'C=US,' \
                          'O=Symantec Corporation,' \
                          'OU=Symantec Trust Network,' \
                          'CN=Symantec Class 3 Secure Server CA - G4'
