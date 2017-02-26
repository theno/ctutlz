'''Validate SCTs using the openssl command line tool (which is "clunky").

A lot of the functionality originally comes and have been learned from the
script sct-verify.py written by Pier Carlo Chiodi:
https://github.com/pierky/sct-verify/blob/master/sct-verify.py (under GPL)

He also described the SCT validation steps very well in his blog:
https://blog.pierky.com/certificate-transparency-manually-verify-sct-with-openssl/
'''

import argparse
import logging
import struct
import sys
from contextlib import contextmanager

from utlz import flo

from ctutlz.log import get_log_list
from ctutlz.sct.scrape import scts_by_tls
from ctutlz.sct.validation import validate_scts
from ctutlz.utils import to_hex


def scts_by_ocsp(*args):
    lgr = logging.getLogger('ctutlz')
    lgr.info('Not implemented (yet)\n')
    return (None, None)


def scts_by_cert(*args):
    lgr = logging.getLogger('ctutlz')
    lgr.info('Not implemented (yet)\n')
    return (None, None)


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
        from ctutlz.utils import digest_from_pem
        assert log.id_der == digest_from_pem(log.key)

    for scrape_scts in actions:
        lgr.info(flo('## {scrape_scts.__name__}\n'))
        ee_cert, scts = scrape_scts(hostname)

        if ee_cert:
            lgr.debug('got certificate\n')

        validations = validate_scts(ee_cert, scts, logs)
        if validations:
            for vdn in validations:
                show_validation(vdn)
        elif ee_cert is not None:
            lgr.info('no SCTs\n')


@contextmanager
def loglevel(level):
    logger = logging.getLogger('ctutlz')
    levels = {}
    for handler in logger.handlers:
        levels[handler] = handler.level
        handler.setLevel(level)
    yield
    for handler in logger.handlers:
        handler.setLevel(levels[handler])


def setup_logging(loglevel):
    logger = logging.getLogger('ctutlz')
    logger.setLevel(logging.DEBUG)
    try:
        # python 2.6
        handler = logging.StreamHandler(stream=sys.stdout)
    except TypeError:
        # since python 2.7
        handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    return logger


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('hostname',  # nargs='+',
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
                     help='only validate SCTs gathered via OCSP status request')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    logger = setup_logging(args.loglevel)
    logger.debug(args)

    hosts = args.hostname
    if type(hosts) == str:
        hosts = [hosts]
    for host in hosts:
        run_actions(host, actions=args.actions)


if __name__ == '__main__':
    main()
