import base64
import logging
import os
import sys
from collections import namedtuple

from utlz import flo

from ctutlz.sct.ee_cert import EndEntityCert
from ctutlz.sct.sct import Sct
from ctutlz.sct.signature_input import create_signature_input
from ctutlz.utils.cmd import run_cmd
from ctutlz.tls.sctlist import TlsExtension18


Extension18Result = namedtuple(
    typename='Extension18Result',
    field_names=[
        'ee_cert',
        'extension_18',
        'hostname',
        'output',
        'exitcode',
        'func_name',
        'timeout',
        'max_try',
        'num_try',
    ]
)


def tls_output_2_eecert_and_extension_18(tls_handshake_output):
    '''Extract PEM encoded end entity certificate and PEM encoded server
    extension 18 (SCT) from `tls_handshake_output` and return them as a tuple.
    '''

    '''lines of the b64 encoded ee-cert'''
    ee_cert = []  # end entity certificate
    ee_cert_append = False

    '''lines of the b64 encoded server extension 18 (SCT)'''
    extension_18 = []
    extension_18_append = False

    for line in tls_handshake_output.split('\n'):
        if line == '-----BEGIN CERTIFICATE-----':
            ee_cert_append = True
        elif line == '-----END CERTIFICATE-----':
            ee_cert_append = False
        elif line == '-----BEGIN SERVERINFO FOR EXTENSION 18-----':
            extension_18_append = True
        elif line == '-----END SERVERINFO FOR EXTENSION 18-----':
            extension_18_append = False
        elif ee_cert_append:
            ee_cert.append(line)
        elif extension_18_append:
            extension_18.append(line)

    ee_cert_b64 = ''.join(ee_cert)
    extension_18_b64 = ''.join(extension_18)

    ee_cert_der = base64.b64decode(ee_cert_b64)
    extension_18_der = base64.b64decode(extension_18_b64)

    return ee_cert_der, extension_18_der


def scrape_tls_extension_18_CLUNKY(hostname, timeout=30, max_try=3):
    '''Try to download the serverinfo extension 18 by doing a TLS handshake and
    return the extracted SCT (decoded; in DER format) or None.
    '''
    func_name = sys._getframe().f_code.co_name  # name of this function
    openssl = os.environ.get('OPENSSL_CMD', 'openssl')
    cmd = flo('{openssl}  s_client  -serverinfo 18  '
              '-connect {hostname}:443  -servername {hostname}')
    lgr = logging.getLogger('ctutlz')
    lgr.debug(flo('run_cmd: {cmd}'))
    res = run_cmd(cmd, timeout, max_try)
    extsn_18 = None
    ee_cert = None
    if res.exitcode == 0:
        ee_cert, extsn_18 = tls_output_2_eecert_and_extension_18(res.stdout_str)
    return Extension18Result(ee_cert, extsn_18, hostname,
                             res.stdout_str + res.stderr_str, res.exitcode,
                             func_name, timeout, max_try, num_try=1)


def scrape_tls_extension_18_pyopenssl(hostname, timeout, max_try=3):
    # idea:
    #  * "manuell" über _lib: SSL_CTX_add_client_custom_ext
    #     etwa so wie:
    #      _lib.SSL_CTX_set_info_callback(self._context, self._info_callback)
    #  * resultat abholen per:
    #    Context.set_info_callback()
    pass


def scrape_tls_extension_18(hostname, timeout=30, max_try=3):
    # FIXME: use pyopenssl instead
    return scrape_tls_extension_18_CLUNKY(**locals())


def scts_by_tls(hostname, timeout=30, max_try=3):
    scts_by_tls.sign_input_func = create_signature_input
    res = scrape_tls_extension_18(hostname, timeout, max_try)
    assert res.extension_18 is not None
    if res.extension_18:
        tls_extension_18 = TlsExtension18(res.extension_18)
        sct_list = tls_extension_18.sct_list
        scts = [Sct(entry.sct_der) for entry in sct_list]
        return EndEntityCert(res.ee_cert), scts
    return EndEntityCert(res.ee_cert), None
