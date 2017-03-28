from ctutlz.utils.tdf_bytes import namedtuple, TdfBytesParser


def test_tdf_bytes():

    def _parse_lv2(tdf):
        with TdfBytesParser(tdf) as parser:
            parser.read('lv2', '!2s')
            return parser.result()

    def _parse_nam_tup(tdf):
        with TdfBytesParser(tdf) as parser:
            parser.read('lv1', '!s')

            parse_lv2 = parser.delegate('_tmp', _parse_lv2)
            parser.res.update(parse_lv2)
            del parser.res['_tmp']

            return parser.result()

    NamTup = namedtuple(
        typename='NamTup',
        lazy_vals={
            '_parse_func': lambda _: _parse_nam_tup,

            'lv1': lambda self: str(self._parse['lv1'], 'utf-8'),
            'lv2': lambda self: str(self._parse['lv2'], 'utf-8'),
        }
    )

    ntup = NamTup(arg=b'ARGUMENT')

    assert ntup.tdf == b'ARG'
    assert ntup._parse_func == _parse_nam_tup
    assert type(ntup._parse) == dict
    assert ntup.lv1 == 'A'
    assert ntup.lv2 == 'RG'
