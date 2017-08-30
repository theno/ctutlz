from ctutlz import rfc6962


def test_parse_log_entry_type_0():
    tdf = b'\x00\x00'

    parse, offset = rfc6962._parse_log_entry_type(tdf)

    assert offset == 2
    assert parse == {
        'tdf': b'\x00\x00',
        'val': 0,
    }


def test_parse_log_entry_type_1():
    tdf = b'\x00\x01'

    parse, offset = rfc6962._parse_log_entry_type(tdf)

    assert offset == 2
    assert parse == {
        'tdf': b'\x00\x01',
        'val': 1,
    }


def test_log_entry_type_0_from_tdf():
    tdf = b'\x00\x00anything'

    log_entry_type = rfc6962.LogEntryType(arg=tdf)

    assert log_entry_type.is_x509_entry is True
    assert log_entry_type.is_precert_entry is False
    assert log_entry_type.tdf == b'\x00\x00'
    assert str(log_entry_type) == 'x509_entry'
    assert log_entry_type._parse == {
        'tdf': b'\x00\x00',
        'val': 0,
    }


def test_log_entry_type_0_from_parse():
    parse = {
        'tdf': b'\x00\x00',
        'val': 0,
    }

    log_entry_type = rfc6962.LogEntryType(arg=parse)

    assert log_entry_type.is_x509_entry is True
    assert log_entry_type.is_precert_entry is False
    assert log_entry_type.tdf == b'\x00\x00'
    assert str(log_entry_type) == 'x509_entry'
    assert log_entry_type._parse == {
        'tdf': b'\x00\x00',
        'val': 0,
    }


def test_log_entry_type_1_from_tdf():
    tdf = b'\x00\x01'

    log_entry_type = rfc6962.LogEntryType(arg=tdf)

    assert log_entry_type.is_x509_entry is False
    assert log_entry_type.is_precert_entry is True
    assert log_entry_type.tdf == b'\x00\x01'
    assert str(log_entry_type) == 'precert_entry'
    assert log_entry_type._parse == {
        'tdf': b'\x00\x01',
        'val': 1,
    }


def test_log_entry_type_1_from_parse():
    parse = {
        'tdf': b'\x00\x01',
        'val': 1,
    }

    log_entry_type = rfc6962.LogEntryType(arg=parse)

    assert log_entry_type.is_x509_entry is False
    assert log_entry_type.is_precert_entry is True
    assert log_entry_type.tdf == b'\x00\x01'
    assert str(log_entry_type) == 'precert_entry'
    assert log_entry_type._parse == {
        'tdf': b'\x00\x01',
        'val': 1,
    }


def test_signature_type_0_from_tdf():
    tdf = b'\x00\x01\x02\x03\x04\x05\x06\x07\x89'

    signature_type = rfc6962.SignatureType(arg=tdf)

    assert signature_type.is_certificate_timestamp is True
    assert signature_type.is_tree_hash is False
    assert signature_type._parse == {
        'tdf': b'\x00',
        'val': 0,
    }


def test_signature_type_0_from_parse():
    parse = {
        'tdf': b'\x00',
        'val': 0,
    }

    signature_type = rfc6962.SignatureType(arg=parse)

    assert signature_type.is_certificate_timestamp is True
    assert signature_type.is_tree_hash is False
    assert signature_type._parse == {
        'tdf': b'\x00',
        'val': 0,
    }


def test_signature_type_1_from_tdf():
    tdf = b'\x01'

    signature_type = rfc6962.SignatureType(arg=tdf)

    assert signature_type.is_certificate_timestamp is False
    assert signature_type.is_tree_hash is True
    assert signature_type._parse == {
        'tdf': b'\x01',
        'val': 1,
    }


def test_signature_type_1_from_parse():
    parse = {
        'tdf': b'\x01',
        'val': 1,
    }

    signature_type = rfc6962.SignatureType(arg=parse)

    assert signature_type.is_certificate_timestamp is False
    assert signature_type.is_tree_hash is True
    assert signature_type._parse == {
        'tdf': b'\x01',
        'val': 1,
    }


def test_version_from_tdf():
    tdf = b'\x00anything'

    version = rfc6962.Version(tdf)

    assert version.is_v1 is True
    assert version._parse == {
        'tdf': b'\x00',
        'val': 0,
    }

    # invalid version number

    invalid_tdf = b'\x10'

    version = rfc6962.Version(invalid_tdf)
    assert version.is_v1 is False
    assert version._parse == {
        'tdf': b'\x10',
        'val': 16,
    }


def test_version_from_parse():
    parse = {
        'val': 0,
        'tdf': b'\x00',
    }

    version = rfc6962.Version(arg=parse)

    assert version.is_v1 is True
    assert version._parse == {
        'tdf': b'\x00',
        'val': 0,
    }


def test_SignedCertificateTimestamp_from_tdf():
    tdf = (b'\x00\xeeK\xbd\xb7u\xce`\xba\xe1Bi\x1f\xab\xe1\x9ef\xa3\x0f~_\xb0r'
           b'\xd8\x83\x00\xc4{\x89z\xa8\xfd\xcb\x00\x00\x01]\xe7\x11\xf5\xf7'
           b'\x00\x00\x04\x03\x00F0D\x02 ph\xa0\x08\x96H\xbc\x1b\x11\x0e\xd0'
           b'\x98\x02\xa8\xac\xb8\x19-|,\xe5\x0e\x9e\xf8/_&\xf7b\x88\xb4U\x02 X'
           b'\xbc\r>jFN\x0e\xda\x0b\x1b\xb5\xc0\x1a\xfd\x90\x91\xb0&\x1b\xdf'
           b'\xdc\x02Z\xd4zd\xd7\x80c\x0f\xd5')

    sct = rfc6962.SignedCertificateTimestamp(arg=tdf)

    assert sct.log_id.tdf == (b'\xeeK\xbd\xb7u\xce`\xba\xe1Bi\x1f\xab\xe1\x9ef'
                              b'\xa3\x0f~_\xb0r\xd8\x83\x00\xc4{\x89z\xa8\xfd'
                              b'\xcb')
    assert sct.tdf == tdf
