import struct

from pyasn1_modules import rfc5280
from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder

from utlz import namedtuple

from ctutlz.utils import sha256_digest


EndEntityCert = namedtuple(
    typename='EndEntityCert',
    field_names=[
        'der',
        'issuer_cert=None',
    ],
    lazy_vals={
        'len': lambda self: len(self.der),
        # cf. https://tools.ietf.org/html/rfc6962#section-3.2      <1..2^24-1>
        'lens': lambda self: struct.unpack('!4B', struct.pack('!I', self.len)),
        'len1': lambda self: self.lens[1],
        'len2': lambda self: self.lens[2],
        'len3': lambda self: self.lens[3],
    }
)


def pyasn1_certificate_from_der(cert_der):
    '''Return pyasn1_modules.rfc2580.Certificate instance parsed from cert_der.
    '''
    cert, _ = der_decoder(cert_der, asn1Spec=rfc5280.Certificate())
    return cert


IssuerCert = namedtuple(
    typename='IssuerCert',
    field_names=[
        'der',
    ],
    lazy_vals={
        'pyasn1': lambda self: pyasn1_certificate_from_der(self.der),
        'pubkey_pyasn1': lambda self:
            self.pyasn1['tbsCertificate']['subjectPublicKeyInfo'],
        'pubkey_der': lambda self: der_encoder(self.pubkey_pyasn1),
        'pubkey_hash': lambda self: sha256_digest(self.pubkey_der),
    }
)
