import collections

from utlz import flo

from utlz import StructContext


_SctListEntry = collections.namedtuple(
    typename='SctListEntry',
    field_names=[
        'sct_len',
        'sct_der',
    ]
)


_TlsExtension18 = collections.namedtuple(
    typename='TlsExtension18',
    field_names=[
        'tls_extension_type',
        'tls_extension_len',
        'signed_certificate_timestamp_list_len',
        'sct_list',
    ]
)


def TlsExtension18(extension_18_tdf):
    with StructContext(extension_18_tdf) as struct:
        data_dict = {
            'tls_extension_type':                    struct.read('!H'),
            'tls_extension_len':                     struct.read('!H'),
            'signed_certificate_timestamp_list_len': struct.read('!H'),
        }
        sct_list = []
        while struct.offset < struct.length:
            sct_len = struct.read('!H')
            sct_der = struct.read(flo('!{sct_len}s'))
            sct_list.append(_SctListEntry(sct_len, sct_der))
        return _TlsExtension18(sct_list=sct_list, **data_dict)


_SignedCertificateTimestampList = collections.namedtuple(
    typename='SignedCertificateTimestampList',
    field_names=[
        'signed_certificate_timestamp_list_len',
        'sct_list',
    ]
)


def SignedCertificateTimestampList(sctlist):
    with StructContext(sctlist) as struct:
        data_dict = {
            'signed_certificate_timestamp_list_len': struct.read('!H'),
        }
        sct_list = []
        while struct.offset < struct.length:
            sct_len = struct.read('!H')
            sct_der = struct.read(flo('!{sct_len}s'))
            sct_list.append(_SctListEntry(sct_len, sct_der))
        return _SignedCertificateTimestampList(sct_list=sct_list, **data_dict)
