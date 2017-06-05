import binascii
import socket
import struct
from functools import reduce

import certifi
import OpenSSL
import pyasn1_modules.rfc2560
import pyasn1_modules.rfc5280
from pyasn1.codec import ber
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.type.univ import ObjectIdentifier, OctetString, Sequence
from utlz import flo, namedtuple

from ctutlz.rfc6962 import SignedCertificateTimestamp
from ctutlz.sct.ee_cert import EndEntityCert, IssuerCert
from ctutlz.tls.sctlist import SignedCertificateTimestampList, TlsExtension18


def scts_from_cert(cert_der):
    '''Return list of SCTs of the SCTList SAN extension of the certificate.

    Args:
        cert_der(bytes): DER encoded ASN.1 Certificate

    Return:
        [<ctutlz.rfc6962.SignedCertificateTimestamp>, ...]
    '''
    cert, _ = der_decoder(
        cert_der, asn1Spec=pyasn1_modules.rfc5280.Certificate())
    sctlist_oid = ObjectIdentifier(value='1.3.6.1.4.1.11129.2.4.2')
    exts = [extension
            for extension
            in cert['tbsCertificate']['extensions']
            if extension['extnID'] == sctlist_oid]

    if len(exts) != 0:
        extension_sctlist = exts[0]
        os_inner_der = extension_sctlist['extnValue']  # type: OctetString()
        os_inner, _ = der_decoder(os_inner_der, OctetString())
        sctlist_hex = os_inner.prettyPrint().split('0x')[-1]
        sctlist_der = binascii.unhexlify(sctlist_hex)

        sctlist = SignedCertificateTimestampList(sctlist_der)
        return [SignedCertificateTimestamp(entry.sct_der)
                for entry
                in sctlist.sct_list]
    return []


def sctlist_hex_from_ocsp_pretty_print(ocsp_resp):
    sctlist_hex = None
    splitted = ocsp_resp.split('<no-name>=1.3.6.1.4.1.11129.2.4.5', 1)
    if len(splitted) > 1:
        _, after = splitted
        _, sctlist_hex_with_rest = after.split('<no-name>=0x', 1)
        sctlist_hex, _ = sctlist_hex_with_rest.split('\n', 1)
    return sctlist_hex


def scts_from_ocsp_resp(ocsp_resp_der):
    '''Return list of SCTs of the OCSP status response.

    Args:
        ocsp_resp_der(bytes): DER encoded OCSP status response

    Return:
        [<ctutlz.rfc6962.SignedCertificateTimestamp>, ...]
    '''
    if ocsp_resp_der:
        ocsp_resp, _ = der_decoder(
            ocsp_resp_der, asn1Spec=pyasn1_modules.rfc2560.OCSPResponse())

        response_bytes = ocsp_resp.getComponentByName('responseBytes')
        # os: octet string
        response_os = response_bytes.getComponentByName('response')

        der_decoder.defaultErrorState = ber.decoder.stDumpRawValue
        response, _ = der_decoder(response_os, Sequence())

        sctlist_os_hex = sctlist_hex_from_ocsp_pretty_print(
            response.prettyPrint())

        if sctlist_os_hex:
            sctlist_os_der = binascii.unhexlify(sctlist_os_hex)
            sctlist_os, _ = der_decoder(sctlist_os_der, OctetString())
            sctlist_hex = sctlist_os.prettyPrint().split('0x')[-1]
            sctlist_der = binascii.unhexlify(sctlist_hex)

            sctlist = SignedCertificateTimestampList(sctlist_der)
            return [SignedCertificateTimestamp(entry.sct_der)
                    for entry
                    in sctlist.sct_list]
    return []


def scts_from_tls_ext_18(tls_ext_18_tdf):
    '''Return list of SCTs of the TLS extension 18 server reply.

    Args:
        tls_ext_18_tdf(bytes): TDF encoded TLS extension 18 server reply.

    Return:
        [<ctutlz.rfc6962.SignedCertificateTimestamp>, ...]
    '''
    scts = []

    if tls_ext_18_tdf:
        tls_extension_18 = TlsExtension18(tls_ext_18_tdf)
        sct_list = tls_extension_18.sct_list

        scts = [SignedCertificateTimestamp(entry.sct_der)
                for entry
                in sct_list]

    return scts


TlsHandshakeResult = namedtuple(
    typename='TlsHandshakeResult',
    field_names=[
        'ee_cert_der',
        'issuer_cert_der',
        'ocsp_resp_der',
        'tls_ext_18_tdf',
    ],
    lazy_vals={
        'ee_cert': lambda self: EndEntityCert(self.ee_cert_der),
        'issuer_cert': lambda self: IssuerCert(self.issuer_cert_der),

        'scts_by_cert': lambda self: scts_from_cert(self.ee_cert_der),
        'scts_by_ocsp': lambda self: scts_from_ocsp_resp(self.ocsp_resp_der),
        'scts_by_tls': lambda self: scts_from_tls_ext_18(self.tls_ext_18_tdf),
    }
)


def create_context(scts_tls, scts_ocsp):
    '''
    Args:
        scts_tls: If True, register callback for TSL extension 18 (for SCTs)
        scts_ocsp: If True, register callback for OCSP-response (for SCTs)
    '''

    def verify_callback(conn, cert, errnum, depth, ok):
        '''Dummy callback.'''
        return 1  # True

    ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
    ctx.set_options(OpenSSL.SSL.OP_NO_SSLv2)
    ctx.set_options(OpenSSL.SSL.OP_NO_SSLv3)

    ctx.set_verify(OpenSSL.SSL.VERIFY_PEER, verify_callback)
    ca_filename = certifi.where()
    ctx.load_verify_locations(ca_filename)

    ctx.tls_ext_18_tdf = None
    if scts_tls:
        from ctutlz.tls.handshake_openssl import ffi, lib

        # this annotation makes the callback function available at
        # lib.serverinfo_cli_parse_cb() of type cdef so it can be used as
        # argument for the call of lib.SSL_CTX_add_client_custom_ext()
        @ffi.def_extern()
        def serverinfo_cli_parse_cb(ssl, ext_type, _in, inlen, al, arg):
            if ext_type == 18:

                def reduce_func(accum_value, current):
                    fmt = accum_value[0] + current[0]
                    values = accum_value[1] + (current[1], )
                    return fmt, values

                initializer = ('!', ())
                fmt, values = reduce(reduce_func, [
                    ('H', ext_type),
                    ('H', inlen),
                    (flo('{inlen}s'), bytes(ffi.buffer(_in, inlen))),
                ], initializer)
                ctx.tls_ext_18_tdf = struct.pack(fmt, *values)
            return 1  # True

        # register callback for TLS extension result into the SSL context
        # created with PyOpenSSL, using OpenSSL "directly"
        if not lib.SSL_CTX_add_client_custom_ext(ffi.cast('struct ssl_ctx_st *',
                                                          ctx._context),
                                                 18,
                                                 ffi.NULL, ffi.NULL, ffi.NULL,
                                                 lib.serverinfo_cli_parse_cb,
                                                 ffi.NULL):
            import sys
            sys.stderr.write('Unable to add custom extension 18\n')
            lib.ERR_print_errors_fp(sys.stderr)
            sys.exit(1)

    ctx.ocsp_resp_der = None
    if scts_ocsp:

        def ocsp_client_callback(connection, ocsp_data, data):
            ctx.ocsp_resp_der = ocsp_data
            return True

        ctx.set_ocsp_client_callback(ocsp_client_callback, data=None)

    return ctx


def create_socket(scts_tls, scts_ocsp):
    '''
    Args:
        scts_tls: If True, register callback for TSL extension 18 (for SCTs)
        scts_ocsp: If True, register callback for OCSP-response (for SCTs)
    '''
    ctx = create_context(scts_tls, scts_ocsp)
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return OpenSSL.SSL.Connection(ctx, raw_sock)


def do_handshake(domain, scts_tls=True, scts_ocsp=True):
    '''
    Args:
        domain: string with domain name,
                for example: 'ritter.vg', or 'www.ritter.vg'
        scts_tls: If True, register callback for TSL extension 18 (for SCTs)
        scts_ocsp: If True, register callback for OCSP-response (for SCTs)
    '''
    sock = create_socket(scts_tls, scts_ocsp)

    sock.request_ocsp()

    ocsp_resp_der = None
    tls_ext_18_tdf = None

    try:
        sock.connect((domain, 443))
        sock.do_handshake()

        # type: OpenSSL.crypto.X509; ee: end entity
        ee_cert_x509 = sock.get_peer_certificate()
        # type: [OpenSSL.crypto.X509, ...]
        chain_x509s = sock.get_peer_cert_chain()
        issuer_cert_x509 = chain_x509s[1]

        ctx = sock.get_context()
        if scts_tls:
            if ctx.tls_ext_18_tdf:
                tls_ext_18_tdf = ctx.tls_ext_18_tdf
        if scts_ocsp:
            if ctx.ocsp_resp_der:
                ocsp_resp_der = ctx.ocsp_resp_der

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        exc_type = type(exc)
        print(flo('### {exc}\n\n{tb}\n\nexc-type: {exc_type}'))
        raise exc
    finally:
        sock.close()  # sock.close() possible?

    ee_cert_der = OpenSSL.crypto.dump_certificate(
        type=OpenSSL.crypto.FILETYPE_ASN1,
        cert=ee_cert_x509)

    # https://tools.ietf.org/html/rfc5246#section-7.4.2
    issuer_cert_der = OpenSSL.crypto.dump_certificate(
        type=OpenSSL.crypto.FILETYPE_ASN1,
        cert=issuer_cert_x509)

    return TlsHandshakeResult(ee_cert_der, issuer_cert_der,
                              ocsp_resp_der, tls_ext_18_tdf)
