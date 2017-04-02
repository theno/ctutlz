# from ctutlz.tls.handshake import cert_of_domain, scts_from_cert

import binascii
import socket

import certifi
import OpenSSL
import pyasn1_modules.rfc5280
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.type.univ import OctetString
from OpenSSL import SSL, crypto
from utlz import flo

from ctutlz.sct.sct import Sct
from ctutlz.tls.sctlist import SignedCertificateTimestampList


def create_context():

    def verify_callback(conn, cert, errnum, depth, ok):
        '''
        Return:
          0 if okay  (like "zero error")
          != 0, else
        '''
        # return bool(ok == 1)
        return True

    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.set_options(SSL.OP_NO_SSLv2)
    ctx.set_options(SSL.OP_NO_SSLv3)

    ctx.set_verify(SSL.VERIFY_PEER, verify_callback)
    ca_filename = certifi.where()
    ctx.load_verify_locations(ca_filename)

    # OCSP

    ctx.ocsp_resps = []

    def ocsp_client_callback(connection, ocsp_data, data):
        ctx.ocsp_resps.append(ocsp_data)
        return True

    ctx.set_ocsp_client_callback(ocsp_client_callback, data=None)

    # TlsExtension18

    ctx.tls_extension_18_resps = []

    # static int serverinfo_cli_parse_cb(SSL *s, unsigned int ext_type,
    #                                    const unsigned char *in, size_t inlen,
    #                                    int *al, void *arg)
    def tls_ext_callback(s, ext_type, _in, inlen, al, arg):
        ctx.tls_extension_18_resps.append(tls_ext_data)

    def cb(*args, **kwargs):
        print('CALLBACK 58')
        #ctx.tls_extension_18_resps.append({'args': args, 'kwargs': kwargs})
        print('CALLBACK 60')

    # ext_type = 18
    ext_type = 18
    add_cb = OpenSSL._util.ffi.NULL
    free_cb = OpenSSL._util.ffi.NULL
    add_arg = OpenSSL._util.ffi.NULL
    parse_cb = OpenSSL._util.ffi.callback('int(*)'
                                          '(SSL *, unsigned int, '
                                          'unsigned char *, size_t, int *, '
                                          'void *)',
                                          cb)
    parse_arg = OpenSSL._util.ffi.NULL
    res = OpenSSL._util.lib.SSL_CTX_add_client_custom_ext(ctx._context,
                                                          ext_type,
                                                          add_cb,
                                                          free_cb,
                                                          add_arg,
                                                          parse_cb,
                                                          parse_arg)
    print('\nres:')
    print(res)
    if bool(res):
        print('okay: SSL_CTX_add_client_custom_ext() call')
    else:
        print('NOT okay: SSL_CTX_add_client_custom_ext() call')
    print('\n----\n')

    return ctx


def create_socket():
    # init openssl, cf. https://en.wikibooks.org/wiki/OpenSSL/Initialization
    OpenSSL._util.lib.SSL_load_error_strings()
    OpenSSL._util.lib.SSL_library_init()
    OpenSSL._util.lib.OpenSSL_add_all_algorithms()
    OpenSSL._util.lib.OPENSSL_config(OpenSSL._util.ffi.NULL)

    ctx = create_context()
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return SSL.Connection(ctx, raw_sock)


def do_handshake(domain):
    sock = create_socket()

    sock.request_ocsp()

    ocsp_response = None

    print(sock.get_context().tls_extension_18_resps)  # TODO DEBUG
    # from pprint import pprint; pprint(dir(sock))

    try:
        print('104')  # TODO DEBUG
        sock.connect((domain, 443))
        print('106')  # TODO DEBUG
        sock.do_handshake()
        print('108')  # TODO DEBUG
        chain = sock.get_peer_cert_chain()
        certificate = sock.get_peer_certificate()

        ctx = sock.get_context()
        if ctx.ocsp_resps:
            ocsp_response = ctx.ocsp_resps[0]
        if ctx.tls_extension_18_resps:
            tls_extension_18_response = ctx.tls_extension_18_resps[0]
        print(ctx.tls_extension_18_resps)  # TODO DEBUG

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        exc_type = type(exc)
        print(flo('### {exc}\n\n{tb}\n\nexc-type: {exc_type}'))
        raise exc
    finally:
        sock.close()  # sock.close() possible?

    return certificate, chain, ocsp_response


def cert_of_domain(domain):
    cert_x509, chain_x509s, ocsp_resp_der = do_handshake(domain)
    cert_der = crypto.dump_certificate(type=crypto.FILETYPE_ASN1,
                                       cert=cert_x509)
    # https://tools.ietf.org/html/rfc5246#section-7.4.2
    issuer_cert_x509 = chain_x509s[1]
    issuer_cert_der = crypto.dump_certificate(type=crypto.FILETYPE_ASN1,
                                              cert=issuer_cert_x509)
    return cert_der, issuer_cert_der, ocsp_resp_der


def scts_from_cert(cert_der):
    cert, _ = der_decoder(cert_der,
                          asn1Spec=pyasn1_modules.rfc5280.Certificate())
    scts = []

    # FIXME: use pyopenssl access method
    exts = [extension
            for extension
            in cert['tbsCertificate']['extensions']
            if str(extension['extnID']) == '1.3.6.1.4.1.11129.2.4.2']

    if len(exts) != 0:
        extension_sctlist = exts[0]

        os_inner_der = extension_sctlist['extnValue']  # type: OctetString()
        os_inner, _ = der_decoder(os_inner_der, OctetString())

        sctlist_hex = os_inner.prettyPrint().split('0x')[-1]  # FIXME: ugly way
        sctlist_der = binascii.unhexlify(sctlist_hex)
        sctlist = SignedCertificateTimestampList(sctlist_der)
        scts = [Sct(entry.sct_der) for entry in sctlist.sct_list]

    return scts
