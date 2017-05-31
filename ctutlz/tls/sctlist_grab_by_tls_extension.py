import sys
from collections import namedtuple

from ctutlz.sct.ee_cert import EndEntityCert
from ctutlz.sct.sct import Sct
from ctutlz.sct.signature_input import create_signature_input
from ctutlz.tls.handshake import cert_of_domain
from ctutlz.tls.sctlist import TlsExtension18


Extension18Result = namedtuple(
    typename='Extension18Result',
    field_names=[
        'ee_cert',
        'extension_18_tdf',
        'hostname',
        'output',
        'exitcode',
        'func_name',
        'timeout',
        'max_try',
        'num_try',
    ]
)


def scrape_tls_extension_18(hostname, timeout=30, max_try=3):
    func_name = sys._getframe().f_code.co_name  # name of this function
    cert_der, issuer_cert_der, ocsp_resp_der, tls_ext_18_tdf = \
        cert_of_domain(hostname)
    return Extension18Result(cert_der, tls_ext_18_tdf, hostname,
                             '', 0,
                             func_name, timeout, max_try, num_try=1)


def scts_by_tls(hostname, timeout=30, max_try=3):
    scts_by_tls.sign_input_func = create_signature_input
    res = scrape_tls_extension_18(hostname, timeout, max_try)
    if res.extension_18_tdf:
        tls_extension_18 = TlsExtension18(res.extension_18_tdf)
        sct_list = tls_extension_18.sct_list
        scts = [Sct(entry.sct_der) for entry in sct_list]
        return EndEntityCert(res.ee_cert), scts
    return EndEntityCert(res.ee_cert), None
