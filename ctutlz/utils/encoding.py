import base64
import hashlib


def encode_to_b64(arg):
    '''Return arg as Base64 encoded string (not as bytes-str).'''
    res = base64.b64encode(arg)
    # assert type(res) == bytes, 'type(result) is ' + str(type(res))
    return res.decode('ascii')


def decode_from_b64(arg):
    return base64.b64decode(arg)


def sha256_digest(arg):
    return hashlib.sha256(arg).digest()


def digest_from_b64(arg):
    return sha256_digest(decode_from_b64(arg))


def digest_from_b64_encoded_to_b64(arg):
    return encode_to_b64(digest_from_b64(arg))
