'''Decompose an ASN.1 certificate into its components tbsCertificate in DER
format, signatureAlgorithm in DER format, and signatureValue as bytes according
to https://tools.ietf.org/html/rfc5280#section-4.1
'''

import argparse
import base64

import pyasn1_modules.rfc5280
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.codec.der.encoder import encode as der_encoder
from utlz import flo

from ctutlz._version import __version__


def create_parser():
    '''Create the `ArgumentParser` for the command `decompose-cert`.'''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--version',
                        action='version',
                        default=False,
                        version=__version__,
                        help='print version number')

    req = parser.add_argument_group('required arguments')
    req.add_argument('--cert',
                     metavar='<filename>',
                     dest='cert_filename',
                     required=True,
                     help='Certificate in PEM, Base64, or DER format')

    parser.add_argument('--tbscert',
                        metavar='<filename>',
                        dest='tbscert_filename',
                        # required=True,
                        help='write extracted tbsCertificate to this file '
                             '(DER encoded)')
    parser.add_argument('--sign-algo',
                        metavar='<filename>',
                        dest='sign_algo_filename',
                        # required=True,
                        help='write extracted signatureAlgorithm to this file '
                             '(DER encoded)')
    parser.add_argument('--signature',
                        metavar='<filename>',
                        dest='sign_value_filename',
                        # required=True,
                        help='write extracted signatureValue to this file')
    return parser


def cert_der_from_data(cert_raw):
    '''Return DER encoded certificate from "raw" certificate data which could be
    encoded as PEM, Base64 (B64) or DER.

    Args:
        cert_raw(bytes):

    Return:
        DER encoded certificate as bytes
    '''
    try:
        # assume PEM or B64 format (str)
        cert_raw_str = cert_raw.decode('ascii')
        cert_b64 = cert_raw_str.split(
            '-----BEGIN CERTIFICATE-----', 1
        )[-1].split(
            '-----END CERTIFICATE-----'
        )[0].strip()
        cert_b64 = ''.join(cert_b64.splitlines())
        cert_der = base64.b64decode(cert_b64)
    except UnicodeDecodeError:
        # no PEM or B64 format; then, assume cert_raw is in DER format (bytes)
        cert_der = cert_raw
    return cert_der


# FIXME: put functionality to here when, refactoring to optionally read from
# stdin and write to stdout
def decompose():
    pass


def main():
    parser = create_parser()
    args = parser.parse_args()

    with open(args.cert_filename, 'rb') as fh:
        cert_raw = fh.read()
    cert_der = cert_der_from_data(cert_raw)
    cert, _ = der_decoder(cert_der,
                          asn1Spec=pyasn1_modules.rfc5280.Certificate())

    if args.tbscert_filename:
        tbscert_der = der_encoder(cert['tbsCertificate'])
        with open(args.tbscert_filename, 'wb') as fh:
            fh.write(tbscert_der)

    if args.sign_algo_filename:
        sign_algo_der = der_encoder(cert['signatureAlgorithm'])
        with open(args.sign_algo_filename, 'wb') as fh:
            fh.write(sign_algo_der)

    if args.sign_value_filename:
        signature_value = cert['signature'].asOctets()
        with open(args.sign_value_filename, 'wb') as fh:
            fh.write(signature_value)


if __name__ == '__main__':
    main()
