'''namedtuple defs which represent the data structures defined in RFC 6962 -
Certificate Transparency.
'''

import struct

from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1_modules import rfc5280
from utlz import flo, namedtuple as namedtuple_utlz

from ctutlz.utils.tdf_bytes import TdfBytesParser, namedtuple
from ctutlz.utils.encoding import decode_from_b64, encode_to_b64
from ctutlz.utils.string import to_hex
from ctutlz.sct.ee_cert import tbscert_without_ct_extensions


# tdf := "TLS Data Format" (cf. https://tools.ietf.org/html/rfc5246#section-4)


# 3.1. Log Entries
# https://tools.ietf.org/html/rfc6962#section-3.1


def _parse_log_entry_type(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('val', '!H')  # (65535) -> 2 bytes
        return parser.result()


LogEntryType = namedtuple(
    typename='LogEntryType',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_log_entry_type,

        'val': lambda self: self._parse['val'],

        'is_x509_entry': lambda self: self.val == 0,
        'is_precert_entry': lambda self: self.val == 1,

        '__str__': lambda self: lambda:
            'x509_entry' if self.is_x509_entry else
            'precert_entry' if self.is_precert_entry else
            flo('<unknown log entry type {self.tdf}>'),
    }
)


def _parse_log_entry(tdf):
    with TdfBytesParser(tdf) as parser:
        entry_type = LogEntryType(
            parser.delegate('entry_type', _parse_log_entry_type))

        # parse entry
        if entry_type.is_x509_entry:
            parser.delegate('entry', _parse_x509_chain_entry)
            parser.res['x509_entry'] = parser.res['entry']
        elif entry_type.is_precert_entry:
            parser.delegate('entry', _parse_precert_chain_entry)
            parser.res['precert_entry'] = parser.res['entry']
        else:
            raise Exception(flo('Unknown entry_type: {entry_type}'))

        return parser.result()


LogEntry = namedtuple(
    typename='LogEntry',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_log_entry,

        'entry_type': lambda self: LogEntryType(self._parse['entry_type']),
        'entry': lambda self:
            ASN1Cert(self._parse['entry'])
                if self.entry_type.is_x509_entry else
            PreCert(self._parse['entry'])
                if self.entry_type.is_precert_entry else
            None,
    }
)


def _parse_asn1_cert(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('len1', '!B')
        parser.read('len2', '!B')
        parser.read('len3', '!B')

        der_len = struct.unpack('=I', struct.pack('!4B',
                                                  0,
                                                  parser.res['len1'],
                                                  parser.res['len2'],
                                                  parser.res['len3']))[0]
        parser.res['der_len'] = der_len
        parser.read('der', flo('!{der_len}s'))

        return parser.result()


ASN1Cert = namedtuple(
    typename='ASN1Cert',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_asn1_cert,

        'der': lambda self: self._parse['der'],
        'pyasn1': lambda self: der_decoder(self.der, rfc5280.Certificate),
    }
)


def _parse_asn1_cert_list(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('len1', '!B')
        parser.read('len2', '!B')
        parser.read('len3', '!B')

        der_list_len = struct.unpack('=I', struct.pack('!4B',
                                                       0,
                                                       parser.res['len1'],
                                                       parser.res['len2'],
                                                       parser.res['len3']))[0]
        der_end_offset = parser.offset + der_list_len

        list_of_parse_asn1_cert = []
        while parser.offset < der_end_offset:
            parse_asn1_cert = parser.delegate(_parse_asn1_cert)
            list_of_parse_asn1_cert.append(parse_asn1_cert)

        parser.res['der_list_len'] = der_list_len
        parser.res['list_of_parse_asn1_cert'] = list_of_parse_asn1_cert

        return parser.result()


ASN1CertList = namedtuple(
    typename='ASN1CertList',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_asn1_cert_list,

        'certs': lambda self: [
            ASN1Cert(parse_asn1_cert)
            for parse_asn1_cert
            in self._parse['list_of_parse_asn1_cert']
        ],
    }
)


def _parse_x509_chain_entry(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.delegate('leaf_certificate', _parse_asn1_cert),
        parser.delegate('certificate_chain', _parse_asn1_cert_list),
        return parser.result()


X509ChainEntry = namedtuple(
    typename='X509ChainEntry',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_x509_chain_entry,

        'leaf_certificate': lambda self:
            ASN1Cert(self._parse['leaf_certificate']),
        'certificate_chain': lambda self:
            ASN1CertList(self._parse['certificate_chain']),
    }
)


def _parse_precert_chain_entry(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.delegate('pre_certificate', _parse_asn1_cert),
        parser.delegate('precert_chain', _parse_asn1_cert_list),
        return parser.result()


PrecertChainEntry = namedtuple(
    typename='PrecertChainEntry',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_precert_chain_entry,

        'pre_certificate': lambda self:
            ASN1Cert(self._parse['pre_certificate']),
        'precertificate_chain': lambda self:
            ASN1CertList(self._parse['precert_chain']),
    }
)


# 3.2 Structure of the Signed Certificate Timestamp
# https://tools.ietf.org/html/rfc6962#section-3.2


def _parse_signature_type(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('val', '!B')
        return parser.result()


SignatureType = namedtuple(
    typename='SignatureType',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_signature_type,

        'val': lambda self: self._parse['val'],

        'is_certificate_timestamp': lambda self: self.val == 0,
        'is_tree_hash': lambda self: self.val == 1,

        '__str__': lambda self: lambda:
            'certificate_timestamp' if self.is_certificate_timestamp else
            'tree_hash' if self.is_tree_hash else
            '<unknown signature type>',
    }
)


def _parse_version(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('val', '!B')
        return parser.result()


Version = namedtuple(
    typename='Version',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_version,

        'val': lambda self: int(self._parse['val']),

        'is_v1': lambda self: self.val == 0,

        '__str__': lambda self: lambda:
            'v1' if self.is_v1 else
            '<unkown version>',
    }
)


def _parse_log_id(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('val', '!32s')
        return parser.result()


LogID = namedtuple(
    typename='LogID',
    lazy_vals={
        '_parse_func': lambda _: _parse_log_id,

        # type: int, '!L', [32]
        # https://docs.python.org/3/library/struct.html#format-characters
        'val': lambda self: bytes(self._parse['val']),
    },
)


def _parse_tbs_certificate(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('len1', '!B')
        parser.read('len2', '!B')
        parser.read('len3', '!B')
        len_der = struct.unpack('=I', struct.pack('!4B',
                                                  0,
                                                  parser.res['len1'],
                                                  parser.res['len2'],
                                                  parser.res['len3']))[0]
        from_ = parser.offset
        parser.offset += len_der
        until = parser.offset
        parser.res['der'] = tdf[from_:until]
        return parser.result()


TBSCertificate = namedtuple(
    typename='TBSCertificate',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_tbs_certificate,

        'der': lambda self: bytes(self._parse['der']),
        'pyasn1': lambda self: der_decoder(self.der,
                                           asn1Spec=rfc5280.TBSCertificate()),

        'len': lambda self: len(self.der),
        'lens': lambda self: struct.unpack('!4B', struct.pack('!I', self.len)),
        'len1': lambda self: self.lens[1],
        'len2': lambda self: self.lens[2],
        'len3': lambda self: self.lens[3],

        'without_ct_extensions': lambda self:
            der_encoder(
                TBSCertificate(tbscert_without_ct_extensions(self.pyasn1))),
    }
)


def _parse_pre_cert(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('issuer_key_hash', '!32s')
        parser.delegate('tbs_certificate', _parse_tbs_certificate)
        return parser.result()


PreCert = namedtuple(
    typename='PreCert',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_pre_cert,

        'issuer_key_hash': lambda self: bytes(self._parse['issuer_key_hash']),
        'tbs_certificate': lambda self:
            TBSCertificate(self._parse['tbs_certificate']),
    }
)


def _parse_ct_extensions(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('len', '!H')
        parser.res['val'] = None  # "Currently, no extensions are specified"
        return parser.result()


CtExtensions = namedtuple(
    typename='CtExtensions',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_ct_extensions,

        'len': lambda self: self._parse['len'],
        'val': lambda self: self._parse['val'],
    }
)


def _parse_signed_certificate_timestamp(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.delegate('version', _parse_version)
        parser.delegate('id', _parse_log_id)
        parser.read('timestamp', '!Q')

        parser.delegate('ct_extensions', _parse_ct_extensions)

        # digitally-signed struct
        parser.read('signature_alg_hash', '!B'),
        parser.read('signature_alg_sign', '!B'),
        signature_len = parser.read('signature_len', '!H')
        parser.read('signature', flo('!{signature_len}s'))

    return parser.result()


SignedCertificateTimestamp = namedtuple(
    typename='SignedCertificateTimestamp',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_signed_certificate_timestamp,

        'version': lambda self: Version(self._parse['version']),
        'id': lambda self: LogID(self._parse['id']),
        'timestamp': lambda self: int(self._parse['timestamp']),
        'extensions': lambda self: CtExtensions(self._parse['ct_extensions']),

        # digitally-signed struct
        # https://tools.ietf.org/html/rfc5246#section-4.7
        'signature_algorithm_hash': lambda self:
            int(self._parse['signature_alg_hash']),
        'signature_algorithm_signature': lambda self:
            int(self._parse['signature_alg_sign']),
        'signature_len': lambda self: int(self._parse['signature_len']),
        'signature': lambda self: bytes(self._parse['signature']),

        'log_id': lambda self: self.id,
        'log_id_b64': lambda self: encode_to_b64(self.log_id.tdf),  # type: str
        'version_hex': lambda self: to_hex(self.version.tdf),
        'timestamp_hex': lambda self: to_hex(self.timestamp),
        'extensions_len': lambda self: self.extensions.len,
        'extensions_len_hex': lambda self: to_hex(self.extensions_len),
        'signature_alg_hash_hex': lambda self:
            to_hex(self.signature_algorithm_hash),
        'signature_alg_sign_hex': lambda self:
            to_hex(self.signature_algorithm_sign),
        'signature_b64': lambda self: encode_to_b64(self.signature),  # str
    }
)


def _parse_signature_input(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.delegate('sct_version', _parse_version)
        parser.delegate('signature_type', _parse_signature_type)

        # rest of the SignatureInput is identical to an TimestampedEntry
        parser.delegate('_tmp', _parse_timestamped_entry)
        parser.res.update(parser.res['_tmp'])
        del parser.res['_tmp']

        return parser.result()


# 'digitally-signed struct' of the SignedCertificateTimestamp
SignatureInput = namedtuple(
    typename='SignatureInput',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_signature_input,

        'sct_version': lambda self: Version(self._parse['sct_version']),
        'signature_type': lambda self:
            SignatureType(self._parse['signature_type']),
        'timestamp': lambda self: int(self._parse['timestamp']),
        'entry_type': lambda self: LogEntryType(self._parse['entry_type']),
        'signed_entry': lambda self:
            ASN1Cert(self._parse['signed_entry'])
                if self.entry_type.is_x509_entry else
            PreCert(self._parse['signed_entry'])
                if self.entry_type.is_precert_entry else
            None,

        'precert_entry': lambda self: self._parse.get('precert_entry', None),
        'x509_entry': lambda self: self._parse.get('x509_entry', None),
    }
)


# 3.4 Merkle Tree
# https://tools.ietf.org/html/rfc6962#section-3.4


def _parse_merkle_leaf_type(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('val', '!B')  # (255)
        return parser.result()


MerkleLeafType = namedtuple(
    typename='MerkleLeafType',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_merkle_leaf_type,

        'val': lambda self: int(self._parse['val']),

        'is_timestamped_entry': lambda self: self.val == 0,

        '__str__': lambda self: lambda:
            'timestamped_entry' if self.is_timestamped_entry else
            '<unkown merkle leaf type>',
    }
)


def _parse_timestamped_entry(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.read('timestamp', '!Q')  # uint64  -> 8 bytes
        entry_type = LogEntryType(
            parser.delegate('entry_type', _parse_log_entry_type))

        # parse leaf_entry
        if entry_type.is_x509_entry:
            parser.delegate('signed_entry', _parse_asn1_cert)
            parser.res['x509_entry'] = parser.res['signed_entry']
        elif entry_type.is_precert_entry:
            parser.delegate('signed_entry', _parse_pre_cert)
            parser.res['precert_entry'] = parser.res['signed_entry']
        else:
            raise Exception(flo('Unknown entry_type number: {entry_type}'))

        # TODO DEBUG ctlog_get_entries.py related (it looks like some log
        #                                          answers are missing
        #                                          the ct_extensions,
        #                                         or an error in parse routines)
        try:
            parser.delegate('extensions', _parse_ct_extensions)
        except struct.error:
            pass

        return parser.result()


TimestampedEntry = namedtuple(
    typename='TimestampedEntry',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_timestamped_entry,

        'timestamp': lambda self: int(self._parse.get('timestamp')),
        'entry_type': lambda self: LogEntryType(self._parse['entry_type']),
        'signed_entry': lambda self:
            ASN1Cert(self._parse['signed_entry'])
                if self.entry_type.is_x509_entry else
            PreCert(self._parse['signed_entry'])
                if self.entry_type.is_precert_entry else
            None,
        'extensions': lambda self: CtExtensions(self._parse.get('extensions')),

        'precert_entry': lambda self: self._parse.get('precert_entry', None),
        'x509_entry': lambda self: self._parse.get('x509_entry', None),
    }
)


def _parse_merkle_tree_leaf(tdf):
    with TdfBytesParser(tdf) as parser:
        parser.delegate('version', _parse_version)
        leaf_type = parser.delegate('leaf_type', _parse_merkle_leaf_type)

        if MerkleLeafType(leaf_type).is_timestamped_entry:
            parser.delegate('leaf_entry', _parse_timestamped_entry)
        else:
            raise Exception('unknown leaf_type: {leaf_type}!')

        return parser.result()


MerkleTreeLeaf = namedtuple(
    typename='MerkleTreeLeaf',
    field_names='arg',
    lazy_vals={
        '_parse_func': lambda _: _parse_merkle_tree_leaf,

        'version': lambda self: Version(self._parse['version']),
        'leaf_type': lambda self: MerkleLeafType(self._parse['leaf_type']),
        'leaf_entry': lambda self: TimestampedEntry(self._parse['leaf_entry']),

        # alias for 'leaf_entry'
        'timestamped_entry': lambda self: self.leaf_entry,

        '__str__': lambda self: lambda:
            self.__repr__(),
    }
)


# 4.6. Retrieve Entries from Log
# https://tools.ietf.org/html/rfc6962#section-4.6

GetEntriesInput = namedtuple_utlz(
    typename='GetEntriesInput',
    field_names=[
        'start',
        'end',
    ],
)


GetEntriesResponseEntry = namedtuple_utlz(
    typename='GetEntriesResponseEntry',
    field_names=[
        'json_dict',
    ],
    lazy_vals={
        # The base-64 encoded MerkleTreeLeaf structure
        'leaf_input_b64': lambda self: self.json_dict['leaf_input'],
        'leaf_input_tdf': lambda self: decode_from_b64(self.leaf_input_b64),
        'leaf_input': lambda self: MerkleTreeLeaf(self.leaf_input_tdf),

        'is_x509_chain_entry': lambda self:
            self.leaf_input.timestamped_entry.entry_type == 0,
        'is_precert_chain_entry': lambda self: not self.is_x509_chain_entry,

        # The base-64 encoded unsigned data pertaining to the log entry.  In the
        # case of an X509ChainEntry, this is the "certificate_chain".  In the
        # case of a PrecertChainEntry, this is the whole "PrecertChainEntry"
        'extra_data_b64': lambda self: self.json_dict['extra_data'],
        'extra_data_tdf': lambda self: decode_from_b64(self.extra_data_b64),
        'extra_data': lambda self:
            X509ChainEntry(self.extra_data_tdf) if self.is_x509_chain_entry else
            PrecertChainEntry(self.extra_data_tdf),

        # '__str__': lambda self: '<GetEntriesResponseEntry>',
    }
)


GetEntriesResponse = namedtuple_utlz(
    typename='GetEntriesResponse',
    field_names=[
        'json_dict',
    ],
    lazy_vals={
        'entries': lambda self: [GetEntriesResponseEntry(entry)
                                 for entry
                                 in self.json_dict['entries']],

        # for convenience
        'first_entry': lambda self: self.entries[0],
    },
)
