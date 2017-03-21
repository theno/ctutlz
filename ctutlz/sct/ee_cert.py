import struct

from pyasn1_modules import rfc5280
from pyasn1.type.univ import ObjectIdentifier
from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder

from utlz import namedtuple

from ctutlz.utils.encoding import sha256_digest


def pyasn1_certificate_from_der(cert_der):
    '''Return pyasn1_modules.rfc5280.Certificate instance parsed from cert_der.
    '''
    cert, _ = der_decoder(cert_der, asn1Spec=rfc5280.Certificate())
    return cert


def copy_pyasn1_instance(instance):
    der = der_encoder(instance)
    copy, _ = der_decoder(der, rfc5280.TBSCertificate())
    return copy


def tbscert_without_sctlist(tbscert):
    '''Return pyasn1_modules.rfc2580.TBSCertificate instance `cert_pyasn1`
    without sctlist extension (OID 1.3.6.1.4.1.11129.2.4.2).
    '''
    sctlist_oid = ObjectIdentifier(value='1.3.6.1.4.1.11129.2.4.2')
    extensions = tbscert['extensions']
    without_sctlist = extensions.subtype()
    for extension in extensions:
        if extension['extnID'] != sctlist_oid:
            without_sctlist.append(extension)
    copy = copy_pyasn1_instance(tbscert)
    copy['extensions'] = without_sctlist
    return copy


EndEntityCert = namedtuple(
    typename='EndEntityCert',
    field_names=[
        'der',
        'issuer_cert=None',  # type: der
    ],
    lazy_vals={
        'len': lambda self: len(self.der),
        # cf. https://tools.ietf.org/html/rfc6962#section-3.2      <1..2^24-1>
        'lens': lambda self: struct.unpack('!4B', struct.pack('!I', self.len)),
        'len1': lambda self: self.lens[1],
        'len2': lambda self: self.lens[2],
        'len3': lambda self: self.lens[3],

        'pyasn1': lambda self: pyasn1_certificate_from_der(self.der),
        'tbscert_pyasn1': lambda self: self.pyasn1['tbsCertificate'],
        'tbscert_without_sctlist_pyasn1': lambda self:
            tbscert_without_sctlist(self.tbscert_pyasn1),

        'tbscert_without_sctlist_der': lambda self: der_encoder(self.tbscert_without_sctlist_pyasn1),

        'tbscert_without_sctlist_len': lambda self: len(self.tbscert_without_sctlist_der),

        'tbscert_without_sctlist_lens': lambda self:
            struct.unpack('!4B', struct.pack('!I', self.tbscert_without_sctlist_len)),

        # cf. https://tools.ietf.org/html/rfc6962#section-3.2      <1..2^24-1>
        'tbscert_without_sctlist_len1': lambda self: self.tbscert_without_sctlist_lens[1],
        'tbscert_without_sctlist_len2': lambda self: self.tbscert_without_sctlist_lens[2],
        'tbscert_without_sctlist_len3': lambda self: self.tbscert_without_sctlist_lens[3],
    }
)


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
