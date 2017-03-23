# -*- coding: utf-8 -*-
from utlz import flo, namedtuple, StructContext

from ctutlz.utils.encoding import encode_to_b64
from ctutlz.utils.string import to_hex


'''Access data of an SCT in DER format by field names.'''
_Sct = namedtuple(
    typename='Sct',
    field_names=[
        'der',  # "raw" SCT data structure; type: bytes

        # "raw" SCT fields; each of type: bytes
        'version',
        'log_id',
        'timestamp',
        'extensions_len',
        'extensions',
        'signature_alg_hash',
        'signature_alg_sign',
        'signature_len',
        'signature',
    ],
    lazy_vals={
        'log_id_b64': lambda self: encode_to_b64(self.log_id),  # type: str
        'version_hex': lambda self: to_hex(self.version),
        'timestamp_hex': lambda self: to_hex(self.timestamp),
        'extensions_len_hex': lambda self: to_hex(self.extensions_len),
        'signature_alg_hash_hex': lambda self: to_hex(self.signature_alg_hash),
        'signature_alg_sign_hex': lambda self: to_hex(self.signature_alg_sign),
    }
)


def Sct(sct_der):
    # cf. https://tools.ietf.org/html/rfc6962#section-3.2
    with StructContext(sct_der) as struct:
        data_dict = {
            'der': sct_der,
            'version':            struct.read('!B'),
            'log_id':             struct.read('!32s'),
            'timestamp':          struct.read('!Q'),
            'extensions_len':     struct.read('!H'),
            'extensions': None,
            'signature_alg_hash': struct.read('!B'),
            'signature_alg_sign': struct.read('!B'),
        }
        signature_len = struct.read('!H')
        signature = struct.read(flo('!{signature_len}s'))
    return _Sct(signature_len=signature_len,
                signature=signature,
                **data_dict)
