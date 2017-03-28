import struct

from utlz import namedtuple as namedtuple_utlz


# tdf := "TLS Data Format" (cf. https://tools.ietf.org/html/rfc5246#section-4)


def namedtuple(typename, field_names='arg', lazy_vals=None, **kwargs):

    lazy_vals['_parse'] = lambda self: \
        self.arg if type(self.arg) == dict else \
        self._parse_func(self.arg)[0] if type(self.arg) == bytes else \
        None

    lazy_vals['tdf'] = lambda self: \
        self._parse['tdf']

    return namedtuple_utlz(typename, field_names, lazy_vals, **kwargs)


class TdfBytesParser(object):
    '''An instance of this is a file like object which enables access of a
    tdf (data) struct (a bytes string).
    '''

    # context methods

    def __init__(self, tdf_bytes):
        self._bytes = tdf_bytes
        self.offset = 0
        '''mutable parse results (read and delegate) dict'''
        self.res = {}

    def __enter__(self):
        self.offset = 0
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.offset = 0
        return

    # methods for parsing

    def read(self, key, fmt):
        data = struct.unpack_from(fmt, self._bytes, self.offset)
        self.offset += struct.calcsize(fmt)
        if len(data) == 1:
            self.res[key] = data[0]
        else:
            self.res[key] = data
        return self.res[key]

    def delegate(self, key, read_func):
        self.res[key], offset = read_func(self._bytes[self.offset:])
        self.offset += offset
        return self.res[key]

    def result(self):
        self.res['tdf'] = bytes(bytearray(self._bytes[0:self.offset]))
        return self.res, self.offset
