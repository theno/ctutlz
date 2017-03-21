'''Validate Signed Certificate Timestamps (SCTs) delivered from one or several
hosts by X.509v3 extension, TLS extension, or OCSP stapling.

A lot of the functionality originally comes and have been learned from the
script sct-verify.py written by Pier Carlo Chiodi:
https://github.com/pierky/sct-verify/blob/master/sct-verify.py (under GPL)

He also described the SCT validation steps very well in his blog:
https://blog.pierky.com/certificate-transparency-manually-verify-sct-with-openssl/
'''

import argparse
import binascii
import logging
import struct

from pyasn1.codec import ber
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.type.univ import Sequence, OctetString
from pyasn1_modules import rfc2560
from utlz import flo, first_paragraph

from ctutlz.tls.handshake import cert_of_domain, scts_from_cert
from ctutlz.ctlog import get_log_list
from ctutlz.sct.ee_cert import EndEntityCert, IssuerCert
from ctutlz.tls.sctlist import SignedCertificateTimestampList
from ctutlz.tls.sctlist_grab_by_tls_extension import scts_by_tls
from ctutlz.sct.sct import Sct
from ctutlz.sct.verification import verify_scts
from ctutlz.sct.signature_input import create_signature_input_precert
from ctutlz.sct.signature_input import create_signature_input
from ctutlz.utils.string import to_hex
from ctutlz.utils.logger import loglevel, setup_logging


def sctlist_hex_from_ocsp_pretty_print(ocsp_resp):
    sctlist_hex = None
    splitted = ocsp_resp.split('<no-name>=1.3.6.1.4.1.11129.2.4.5', 1)
    if len(splitted) > 1:
        _, after = splitted
        _, sctlist_hex_with_rest = after.split('<no-name>=0x', 1)
        sctlist_hex, _ = sctlist_hex_with_rest.split('\n', 1)
    return sctlist_hex


def scts_by_ocsp(hostname):
    scts_by_ocsp.sign_input_func = create_signature_input

    scts = []
    cert_der, issuer_cert_der, ocsp_resp_der = cert_of_domain(hostname)
    if ocsp_resp_der:
        ocsp_resp, _ = der_decoder(ocsp_resp_der, rfc2560.OCSPResponse())

        responseBytes = ocsp_resp.getComponentByName('responseBytes')
        response_os = responseBytes.getComponentByName('response')

        der_decoder.defaultErrorState = ber.decoder.stDumpRawValue
        response, _ = der_decoder(response_os, Sequence())

        sctlist_os_hex = sctlist_hex_from_ocsp_pretty_print(response.prettyPrint())

        if sctlist_os_hex:
            sctlist_os_der = binascii.unhexlify(sctlist_os_hex)
            # open('sctlist_by_ocsp', 'wb').write(sctlist_os_der)
            sctlist_os, _ = der_decoder(sctlist_os_der, OctetString())

            sctlist_hex = sctlist_os.prettyPrint().split('0x')[-1]  # FIXME: ugly way
            sctlist_der = binascii.unhexlify(sctlist_hex)
            sctlist = SignedCertificateTimestampList(sctlist_der)
            scts = [Sct(entry.sct_der) for entry in sctlist.sct_list]

    return EndEntityCert(cert_der, IssuerCert(issuer_cert_der)), scts


def scts_by_cert(hostname):
    scts_by_cert.sign_input_func = create_signature_input_precert
    cert_der, issuer_cert_der, ocsp_resp_der = cert_of_domain(hostname)
    scts = scts_from_cert(cert_der)
    return EndEntityCert(cert_der,
                         issuer_cert=IssuerCert(issuer_cert_der)), scts


def show_signature(sct):
    lgr = logging.getLogger('ctutlz')
    sig_offset = 0
    while sig_offset < len(sct.signature):
        if len(sct.signature) - sig_offset > 16:
            bytes_to_read = 16
        else:
            bytes_to_read = len(sct.signature) - sig_offset
        sig_bytes = struct.unpack_from(flo('!{bytes_to_read}s'),
                                       sct.signature,
                                       sig_offset)[0]
        if sig_offset == 0:
            lgr.info('Signature : %s' % to_hex(sig_bytes))
        else:
            lgr.info('            %s' % to_hex(sig_bytes))
        sig_offset = sig_offset + bytes_to_read


def show_validation(vdn):
    sct = vdn.sct

    lgr = logging.getLogger('ctutlz')
    sct_log_id1, sct_log_id2 = [to_hex(val)
                                for val
                                in struct.unpack("!16s16s", sct.log_id)]
    lgr.info('=' * 59)
    lgr.info(flo('Version   : {sct.version_hex}'))
    lgr.info(flo('LogID     : {sct_log_id1}'))
    lgr.info(flo('            {sct_log_id2}'))
    with loglevel(logging.INFO):
        lgr.info(flo('LogID b64 : {sct.log_id_pem}'))
    lgr.info(flo('Timestamp : {sct.timestamp} ({sct.timestamp_hex})'))
    lgr.info(flo('Extensions: {sct.extensions_len} ({sct.extensions_len_hex})'))
    lgr.info(flo('Algorithms: {sct.signature_alg_hash_hex}/'
                 '{sct.signature_alg_sign} (hash/sign)'))

    show_signature(sct)

    log = vdn.log
    with loglevel(logging.INFO):
        if log is None:
            lgr.info('Log not found\n')
        else:
            lgr.info(flo('Log found : {log.description}'))
    if log is not None:
        lgr.info('Operator  : ' + ', '.join(log.operated_by))

    with loglevel(logging.INFO):
        if vdn.output:
            lgr.info(flo('Result    : {vdn.output}'))

    # FIXME: show openssl return value on error
    if vdn.cmd_res is not None:
        lgr.debug(str(vdn.cmd_res._asdict().get('cmd', '')) + '\n')


def run_actions(hostname, actions):
    lgr = logging.getLogger('ctutlz')
    with loglevel(logging.INFO):
        lgr.info(flo('# {hostname}\n'))

    logs = get_log_list()  # FIXME make as argument
    # TODO DEBUG
    for log in logs:
        from ctutlz.utils.encoding import digest_from_pem
        assert log.id_der == digest_from_pem(log.key)

    for scrape_scts in actions:
        with loglevel(logging.INFO):
            lgr.info(flo('## {scrape_scts.__name__}\n'))
        issuer_cert = None
        ee_cert, scts = scrape_scts(hostname)
        if ee_cert:
            lgr.debug('got certificate\n')

            # FIXME: kinda hacky, un-pythonic
            # IssuerCert or None
            issuer_cert = ee_cert.issuer_cert

        validations = verify_scts(ee_cert, scts, logs, issuer_cert,
                                  sign_input_func=scrape_scts.sign_input_func)
        if validations:
            for vdn in validations:
                show_validation(vdn)
        elif ee_cert is not None:
            lgr.info('no SCTs\n')


def create_parser():
    parser = argparse.ArgumentParser(description=first_paragraph(__doc__))
    parser.add_argument('hostname',
                        nargs='+',
                        help="host name of the server (example: 'ritter.vg')")

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument('--short',
                     dest='loglevel',
                     action='store_const',
                     const=logging.WARNING,
                     default=logging.INFO,  # default loglevel if nothing set
                     help='show short result and warnings/errors only')
    meg.add_argument('--debug',
                     dest='loglevel',
                     action='store_const',
                     const=logging.DEBUG,
                     help='show more for diagnostic purposes')

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument('--cert-only',
                     dest='actions',
                     action='store_const',
                     const=[scts_by_cert],
                     default=[scts_by_cert, scts_by_tls, scts_by_ocsp],
                     help='only validate SCTs included in the certificate')
    meg.add_argument('--tls-only',
                     dest='actions',
                     action='store_const',
                     const=[scts_by_tls],
                     help='only validate SCTs gathered from TLS handshake')
    meg.add_argument('--ocsp-only',
                     dest='actions',
                     action='store_const',
                     const=[scts_by_ocsp],
                     help='only validate SCTs gathered via OCSP request')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    logger = setup_logging(args.loglevel)
    logger.debug(args)

    for host in args.hostname:
        run_actions(host, actions=args.actions)


if __name__ == '__main__':
    main()
