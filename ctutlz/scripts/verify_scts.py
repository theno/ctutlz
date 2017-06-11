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

from utlz import flo, first_paragraph, text_with_newlines

from ctutlz.tls.handshake import do_handshake
from ctutlz.ctlog import download_log_list, get_log_list, read_log_list
from ctutlz.sct.verification import verify_scts
from ctutlz.sct.signature_input import create_signature_input_precert
from ctutlz.sct.signature_input import create_signature_input
from ctutlz.utils.string import to_hex
from ctutlz.utils.logger import VERBOSE, init_logger, setup_logging, logger


def verify_scts_by_cert(res, ctlogs):
    '''
    Args:
        res(ctutlz.tls.TlsHandshakeResult)
        ctlogs([<ctutlz.ctlog.Log>, ...])

    Return:
        [<ctutlz.sct.verification.SctVerificationResult>, ...]
    '''
    return verify_scts(res.ee_cert,
                       res.scts_by_cert,
                       ctlogs,
                       res.issuer_cert,
                       create_signature_input_precert)


def verify_scts_by_tls(res, ctlogs):
    '''
    Args:
        res(ctutlz.tls.TlsHandshakeResult)
        ctlogs([<ctutlz.ctlog.Log>, ...])

    Return:
        [<ctutlz.sct.verification.SctVerificationResult>, ...]
    '''
    return verify_scts(res.ee_cert,
                       res.scts_by_tls,
                       ctlogs,
                       res.issuer_cert,
                       create_signature_input)


def verify_scts_by_ocsp(res, ctlogs):
    '''
    Args:
        res(ctutlz.tls.TlsHandshakeResult)
        ctlogs([<ctutlz.ctlog.Log>, ...])

    Return:
        [<ctutlz.sct.verification.SctVerificationResult>, ...]
    '''
    return verify_scts(res.ee_cert,
                       res.scts_by_ocsp,
                       ctlogs,
                       res.issuer_cert,
                       create_signature_input)


# for more convenient command output
verify_scts_by_cert.__name__ = 'SCTs by Certificate'
verify_scts_by_tls.__name__ = 'SCTs by TLS'
verify_scts_by_ocsp.__name__ = 'SCTs by OCSP'


def show_signature_verbose(signature):
    '''Print out signature as hex string to logger.verbose.

    Args:
        signature(bytes)
    '''
    sig_offset = 0
    while sig_offset < len(signature):
        if len(signature) - sig_offset > 16:
            bytes_to_read = 16
        else:
            bytes_to_read = len(signature) - sig_offset
        sig_bytes = struct.unpack_from(flo('!{bytes_to_read}s'),
                                       signature,
                                       sig_offset)[0]
        if sig_offset == 0:
            logger.verbose('Signature : %s' % to_hex(sig_bytes))
        else:
            logger.verbose('            %s' % to_hex(sig_bytes))
        sig_offset = sig_offset + bytes_to_read


def show_verification(verification):
    '''
    Args:
        verification(ctutlz.sct.verification.SctVerificationResult)
    '''
    sct = verification.sct

    sct_log_id1, sct_log_id2 = [to_hex(val)
                                for val
                                in struct.unpack("!16s16s", sct.log_id.tdf)]
    logger.info('```')
    logger.verbose('=' * 59)
    logger.verbose(flo('Version   : {sct.version_hex}'))
    logger.verbose(flo('LogID     : {sct_log_id1}'))
    logger.verbose(flo('            {sct_log_id2}'))
    logger.info(flo('LogID b64 : {sct.log_id_b64}'))
    logger.verbose(flo('Timestamp : {sct.timestamp} ({sct.timestamp_hex})'))
    logger.verbose(flo(
        'Extensions: {sct.extensions_len} ({sct.extensions_len_hex})'))
    logger.verbose(flo('Algorithms: {sct.signature_alg_hash_hex}/'
                       '{sct.signature_algorithm_signature} (hash/sign)'))

    show_signature_verbose(sct.signature)
    prefix = 'Sign. b64 : '
    logger.info(prefix + text_with_newlines(sct.signature_b64, line_length=16*3,
                                            newline='\n' + ' '*len(prefix)))

    logger.verbose('--')  # visual gap between sct infos and verification result

    log = verification.log
    if log is None:
        logger.info('Log not found\n')
    else:
        logger.info(flo('Log found : {log.description}'))
        logger.verbose('Operator  : ' + ', '.join(log.operated_by))

    if verification.verified:
        logger.info(flo('Result    : Verified OK'))
    else:
        logger.info(flo('Result    : Verification Failure'))

    logger.info('```\n')


def scrape_and_verify_scts(hostname, verification_tasks, ctlogs):
    logger.info(flo('# {hostname}\n'))

    res = do_handshake(hostname,
                       scts_tls=(verify_scts_by_tls in verification_tasks),
                       scts_ocsp=(verify_scts_by_ocsp in verification_tasks))
    if res.ee_cert_der:
        logger.debug('got certificate\n')

    for verification_task in verification_tasks:
        logger.info(flo('## {verification_task.__name__}\n'))
        verifications = verification_task(res, ctlogs)
        if verifications:
            for verification in verifications:
                show_verification(verification)
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
                     help='show short results and warnings/errors only')
    meg.add_argument('--debug',
                     dest='loglevel',
                     action='store_const',
                     const=logging.DEBUG,
                     help='show more for diagnostic purposes')

    meg1 = parser.add_mutually_exclusive_group()
    meg1.add_argument('--cert-only',
                      dest='verification_tasks',
                      action='store_const',
                      const=[verify_scts_by_cert],
                      default=[verify_scts_by_cert,
                               verify_scts_by_tls,
                               verify_scts_by_ocsp],
                      help='only verify SCTs included in the certificate')
    meg1.add_argument('--tls-only',
                      dest='verification_tasks',
                      action='store_const',
                      const=[verify_scts_by_tls],
                      help='only verify SCTs gathered from TLS handshake')
    meg1.add_argument('--ocsp-only',
                      dest='verification_tasks',
                      action='store_const',
                      const=[verify_scts_by_ocsp],
                      help='only verify SCTs gathered via OCSP request')

    meg2 = parser.add_mutually_exclusive_group()
    meg2.add_argument('--log-list',
                      dest='log_list_filename',
                      metavar='<filename>',
                      help='filename of a log list in JSON format')
    meg2.add_argument('--latest-logs',
                      dest='fetch_ctlogs',
                      action='store_const',
                      const=download_log_list,
                      default=get_log_list,
                      help='for SCT verification against known CT Logs '
                           "(compliant with Chome's CT policy) "
                           'download latest version of '
                           'https://www.certificate-transparency.org/'
                           'known-logs/all_logs_list.json '
                           '-- use built-in log list from 2017-06-05 '
                           'if --latest-logs or --log-list are not set')
    return parser


def main():
    init_logger()
    parser = create_parser()
    args = parser.parse_args()
    setup_logging(args.loglevel)
    logger.debug(args)

    ctlogs = args.fetch_ctlogs()
    if args.log_list_filename:
        ctlogs = read_log_list(args.log_list_filename)

    for host in args.hostname:
        scrape_and_verify_scts(host, args.verification_tasks, ctlogs)


if __name__ == '__main__':
    # when calling `verify-scts` directly from source as pointed out in the
    # README.md (section Devel-Commands) the c-code part needs to be compiled,
    # else the import of the c-module `ctutlz.tls.handshake_openssl` would fail.
    import ctutlz.tls.handshake_openssl_build
    ctutlz.tls.handshake_openssl_build.compile()

    main()
