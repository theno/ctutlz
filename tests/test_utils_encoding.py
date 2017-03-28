from ctutlz.utils.encoding import decode_from_b64


def test_decode_from_b64():
    data = [
        {
            'input': 'ZGF0YSB0byBiZSBlbmNvZGVk',
            'must': b'data to be encoded',
        }
    ]
    for test in data:
        got = decode_from_b64(test['input'])
        assert got == test['must']
