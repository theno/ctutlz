import base64
import hashlib


def encode_to_pem(arg):
    '''Return arg as PEM encoded string (not as bytes-str).'''
    res = base64.b64encode(arg)
    # assert type(res) == bytes, 'type(result) is ' + str(type(res))
    return res.decode('ascii')


def decode_from_pem(arg):
    return base64.b64decode(arg)


def sha256_digest(arg):
    return hashlib.sha256(arg).digest()


def digest_from_pem(arg):
    return sha256_digest(decode_from_pem(arg))


def digest_from_pem_encoded_to_pem(arg):
    return encode_to_pem(digest_from_pem(arg))
