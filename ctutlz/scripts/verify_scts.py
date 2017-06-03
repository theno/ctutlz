'''Verify Signed Certificate Timestamps (SCTs) delivered from one or several
hosts by X.509v3 extension, TLS extension, or OCSP stapling.

A lot of the functionality originally comes and have been learned from the
script sct-verify.py written by Pier Carlo Chiodi:
https://github.com/pierky/sct-verify/blob/master/sct-verify.py (under GPL)

He also described the SCT verification steps very well in his blog:
https://blog.pierky.com/certificate-transparency-manually-verify-sct-with-openssl/
'''

import argparse
import logging
import struct

from utlz import flo, first_paragraph

from ctutlz.tls.handshake import do_handshake
from ctutlz.ctlog import get_log_list
from ctutlz.sct.ee_cert import EndEntityCert, IssuerCert
from ctutlz.sct.verification import verify_scts
from ctutlz.sct.signature_input import create_signature_input_precert
from ctutlz.sct.signature_input import create_signature_input
from ctutlz.utils.string import to_hex
from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger


def scts_by_tls():
    pass  # enum


def scts_by_ocsp():
    pass  # enum


def scts_by_cert():
    pass  # enum


def show_signature(sct):
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
            logger.verbose('Signature : %s' % to_hex(sig_bytes))
        else:
            logger.verbose('            %s' % to_hex(sig_bytes))
        sig_offset = sig_offset + bytes_to_read


def show_signature_b64(sct):
    logger.info(flo('Sign. b64 : {sct.signature_b64}'))


def show_verifications(vdn):
    sct = vdn.sct

    sct_log_id1, sct_log_id2 = [to_hex(val)
                                for val
                                in struct.unpack("!16s16s", sct.log_id)]
    logger.verbose('=' * 59)
    logger.verbose(flo('Version   : {sct.version_hex}'))
    logger.verbose(flo('LogID     : {sct_log_id1}'))
    logger.verbose(flo('            {sct_log_id2}'))
    logger.info(flo('LogID b64 : {sct.log_id_b64}'))
    logger.verbose(flo('Timestamp : {sct.timestamp} ({sct.timestamp_hex})'))
    logger.verbose(flo(
        'Extensions: {sct.extensions_len} ({sct.extensions_len_hex})'))
    logger.verbose(flo('Algorithms: {sct.signature_alg_hash_hex}/'
                       '{sct.signature_alg_sign} (hash/sign)'))

    show_signature(sct)
    show_signature_b64(sct)

    log = vdn.log
    if log is None:
        logger.info('Log not found\n')
    else:
        logger.info(flo('Log found : {log.description}'))
        logger.verbose('Operator  : ' + ', '.join(log.operated_by))

    if vdn.output:
        logger.info(flo('Result    : {vdn.output}'))

    # FIXME: show openssl return value on error
    if vdn.cmd_res is not None:
        logger.debug(str(vdn.cmd_res._asdict().get('cmd', '')) + '\n')


def scrape_and_verify_scts(hostname, actions):
    logger.info(flo('# {hostname}\n'))

    ctlogs = get_log_list()  # FIXME make as argument
    # FIXME: belongs into ctlog.py
    for log in ctlogs:
        from ctutlz.utils.encoding import digest_from_b64
        assert log.id_der == digest_from_b64(log.key)

    res = do_handshake(hostname,
                       scts_tls=(scts_by_tls in actions),
                       scts_ocsp=(scts_by_ocsp in actions))
    if res.ee_cert_der:
        logger.debug('got certificate\n')

    for action in actions:
        logger.info(flo('## {action.__name__}\n'))
        if action is scts_by_cert:
            verifications = verify_scts(EndEntityCert(res.ee_cert_der),
                                        res.scts_by_cert,
                                        ctlogs,
                                        IssuerCert(res.issuer_cert_der),
                                        create_signature_input_precert)
        if action is scts_by_tls:
            verifications = verify_scts(EndEntityCert(res.ee_cert_der),
                                        res.scts_by_tls,
                                        ctlogs,
                                        IssuerCert(res.issuer_cert_der),
                                        create_signature_input)
        if action is scts_by_ocsp:
            verifications = verify_scts(EndEntityCert(res.ee_cert_der),
                                        res.scts_by_ocsp,
                                        ctlogs,
                                        IssuerCert(res.issuer_cert_der),
                                        create_signature_input)
        if verifications:
            for vdn in verifications:
                show_verifications(vdn)
        elif res.ee_cert_der is not None:
            logger.info('no SCTs\n')


def create_parser():
    parser = argparse.ArgumentParser(description=first_paragraph(__doc__))
    parser.add_argument('hostname',
                        nargs='+',
                        help="host name of the server (example: 'ritter.vg')")

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument('--short',
                     dest='loglevel',
                     action='store_const',
                     const=logging.INFO,
                     default=VERBOSE,  # default loglevel if nothing set
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
                     help='only verify SCTs included in the certificate')
    meg.add_argument('--tls-only',
                     dest='actions',
                     action='store_const',
                     const=[scts_by_tls],
                     help='only verify SCTs gathered from TLS handshake')
    meg.add_argument('--ocsp-only',
                     dest='actions',
                     action='store_const',
                     const=[scts_by_ocsp],
                     help='only verify SCTs gathered via OCSP request')
    return parser


def main():
    init_logger()
    parser = create_parser()
    args = parser.parse_args()
    setup_logging(args.loglevel)
    logger.debug(args)

    for host in args.hostname:
        scrape_and_verify_scts(host, actions=args.actions)


if __name__ == '__main__':
    # when calling `verify-scts` directly from source as pointed out in the
    # README.md (section Devel-Commands) the c-code part needs to be compiled,
    # else the import of the c-module `ctutlz.tls.handshake_openssl` would fail.
    import ctutlz.tls.handshake_openssl_build
    ctutlz.tls.handshake_openssl_build.compile()

    main()
