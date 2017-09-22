import struct

import OpenSSL
import pyasn1.error
from pyasn1_modules import rfc5280
from pyasn1.type.univ import ObjectIdentifier, Sequence
from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder

from utlz import namedtuple

from ctutlz.utils.string import string_without_prefix
from ctutlz.utils.encoding import sha256_digest


# https://hg.mozilla.org/mozilla-central/file/tip/security/certverifier/ExtendedValidation.cpp
EV_OIDs = ['1.2.392.200091.100.721.1',
           '1.3.6.1.4.1.6334.1.100.1',
           '2.16.756.1.89.1.2.1.1',
           '1.3.6.1.4.1.23223.1.1.1',
           '1.3.6.1.4.1.23223.1.1.1',
           '1.3.6.1.4.1.23223.1.1.1',
           '2.16.840.1.113733.1.7.23.6',
           '1.3.6.1.4.1.14370.1.6',
           '2.16.840.1.113733.1.7.48.1',
           '2.16.840.1.114404.1.1.2.4.1',
           '2.16.840.1.114404.1.1.2.4.1',
           '2.16.840.1.114404.1.1.2.4.1',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '2.16.840.1.114413.1.7.23.3',
           '2.16.840.1.114413.1.7.23.3',
           '2.16.840.1.114414.1.7.23.3',
           '2.16.840.1.114414.1.7.23.3',
           '2.16.840.1.114412.2.1',
           '1.3.6.1.4.1.8024.0.2.100.1.2',
           '1.3.6.1.4.1.782.1.2.1.8.1',
           '2.16.840.1.114028.10.1.2',
           '1.3.6.1.4.1.4146.1.1',
           '1.3.6.1.4.1.4146.1.1',
           '1.3.6.1.4.1.4146.1.1',
           '2.16.578.1.26.1.3.3',
           '1.3.6.1.4.1.22234.2.5.2.3.1',
           '1.3.6.1.4.1.17326.10.14.2.1.2',
           '1.3.6.1.4.1.17326.10.8.12.1.2',
           '1.3.6.1.4.1.34697.2.1',
           '1.3.6.1.4.1.34697.2.2',
           '1.3.6.1.4.1.34697.2.3',
           '1.3.6.1.4.1.34697.2.4',
           '1.2.616.1.113527.2.5.1.1',
           '1.2.616.1.113527.2.5.1.1',
           '1.3.6.1.4.1.14777.6.1.1',
           '1.3.6.1.4.1.14777.6.1.2',
           '1.3.6.1.4.1.7879.13.24.1',
           '1.3.6.1.4.1.40869.1.1.22.3',
           '1.3.6.1.4.1.4788.2.202.1',
           '2.16.840.1.113733.1.7.23.6',
           '1.3.6.1.4.1.14370.1.6',
           '2.16.840.1.113733.1.7.48.1',
           '1.3.6.1.4.1.13177.10.1.3.10',
           '1.3.6.1.4.1.40869.1.1.22.3',
           '2.16.792.3.0.4.1.1.4',
           '1.3.159.1.17.1',
           '1.3.6.1.4.1.36305.2',
           '1.3.6.1.4.1.36305.2',
           '2.16.840.1.114412.2.1',
           '2.16.840.1.114412.2.1',
           '2.16.840.1.114412.2.1',
           '2.16.840.1.114412.2.1',
           '2.16.840.1.114412.2.1',
           '1.3.6.1.4.1.8024.0.2.100.1.2',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '1.3.6.1.4.1.6449.1.2.1.5.1',
           '1.3.6.1.4.1.4146.1.1',
           '2.16.840.1.114028.10.1.2',
           '2.16.528.1.1003.1.2.7',
           '2.16.840.1.114028.10.1.2',
           '2.16.840.1.114028.10.1.2',
           '2.16.156.112554.3',
           '1.3.6.1.4.1.36305.2',
           '1.3.6.1.4.1.36305.2',
           '1.2.392.200091.100.721.1',
           '2.16.756.5.14.7.4.8',
           '1.3.6.1.4.1.22234.3.5.3.1',
           '1.3.6.1.4.1.22234.3.5.3.2',
           '1.3.6.1.4.1.22234.2.14.3.11',
           '1.3.6.1.4.1.22234.2.14.3.11',
           '1.3.6.1.4.1.22234.2.14.3.11',
           '2.16.840.1.113733.1.7.23.6',
           '2.23.140.1.1',
           '2.23.140.1.1',
           '2.23.140.1.1',
           '2.23.140.1.1',
           '2.23.140.1.1',
           '1.3.171.1.1.10.5.2']


def is_ev_cert(ee_cert):
    '''Return True if ee_cert is an extended validation certificate, else False.

    Args:
        ee_cert (EndEntityCert)
    '''
    oids = []
    oid_certificate_policies = ObjectIdentifier('2.5.29.32')

    all_extensions = ee_cert.tbscert.pyasn1['extensions']
    if all_extensions is not None:
        policy_extensions = [ext
                             for ext
                             in all_extensions
                             if ext['extnID'] == oid_certificate_policies]
        if len(policy_extensions) > 0:
            policy_extension = policy_extensions[0]
            sequence_der = policy_extension['extnValue']  # type: Sequence()
            try:
                sequence, _ = der_decoder(sequence_der, Sequence())
            except pyasn1.error.PyAsn1Error:
                sequence = []  # invalid encoded certificate policy extension

            for idx in range(len(sequence)):
                inner_sequence = sequence.getComponentByPosition(idx)
                oid = inner_sequence.getComponentByPosition(0)
                oids.append(str(oid))

    intersection = list(set(oids) & set(EV_OIDs))
    return intersection != []


def is_letsencrypt_cert(ee_cert):
    '''Return True if ee_cert was issued by Let's Encrypt.

    Args:
        ee_cert (EndEntityCert)
    '''
    organization_name_oid = ObjectIdentifier(value='2.5.4.10')
    issuer = ee_cert.tbscert.pyasn1['issuer']
    if issuer:
        for rdn in issuer['rdnSequence']:
            for item in rdn:
                if item.getComponentByName('type') == organization_name_oid:
                    organisation_name = str(item.getComponentByName('value'))
                    organisation_name = string_without_prefix('\x13\r',
                                                              organisation_name)
                    if organisation_name == "Let's Encrypt":
                        return True
    return False


def pyasn1_certificate_from_der(cert_der):
    '''Return pyasn1_modules.rfc5280.Certificate instance parsed from cert_der.
    '''
    cert, _ = der_decoder(cert_der, asn1Spec=rfc5280.Certificate())
    return cert


def copy_pyasn1_instance(instance):
    der = der_encoder(instance)
    copy, _ = der_decoder(der, rfc5280.TBSCertificate())
    return copy


def pyopenssl_certificate_from_der(cert_der):
    '''Return OpenSSL.crypto.X509 instance parsed from cert_der.
    '''
    cert = OpenSSL.crypto.load_certificate(type=OpenSSL.crypto.FILETYPE_ASN1,
                                           buffer=cert_der)
    return cert


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


def tbscert_without_ct_extensions(tbscert):
    '''Return pyasn1_modules.rfc5280.TBSCertificate instance `cert_pyasn1`
    without sctlist extension (OID 1.3.6.1.4.1.11129.2.4.3) and
    poison extension (OID 1.3.6.1.4.1.11129.2.4.2), if any.
    '''
    sctlist_oid = ObjectIdentifier(value='1.3.6.1.4.1.11129.2.4.2')
    poison_oid = ObjectIdentifier(value='1.3.6.1.4.1.11129.2.4.3')
    ct_oids = [sctlist_oid, poison_oid]

    extensions = tbscert['extensions']
    without_ct_extensions = extensions.subtype()
    for extension in extensions:
        if extension['extnID'] not in ct_oids:
            without_ct_extensions.append(extension)
    copy = copy_pyasn1_instance(tbscert)
    copy['extensions'] = without_ct_extensions
    return copy


TbsCert = namedtuple(
    typename='TbsCert',
    field_names=[
        'pyasn1',
    ],
    lazy_vals={
        'der': lambda self: der_encoder(self.pyasn1),
        'len': lambda self: len(self.der),
        'lens': lambda self: struct.unpack('!4B', struct.pack('!I', self.len)),
        # cf. https://tools.ietf.org/html/rfc6962#section-3.2      <1..2^24-1>
        'len1': lambda self: self.lens[1],
        'len2': lambda self: self.lens[2],
        'len3': lambda self: self.lens[3],

        'without_ct_extensions':
            lambda self: TbsCert(tbscert_without_ct_extensions(self.pyasn1)),
    }
)


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
        'tbscert': lambda self: TbsCert(self.pyasn1['tbsCertificate']),

        # FIXME: YAGNI?
        'pyopenssl': lambda self: pyopenssl_certificate_from_der(self.der),

        'is_ev_cert': lambda self: is_ev_cert(self),
        'is_letsencrypt_cert': lambda self: is_letsencrypt_cert(self),
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
