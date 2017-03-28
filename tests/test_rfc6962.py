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
