# from ctutlz.tls.handshake import cert_of_domain, scts_from_cert

import binascii
import socket

import certifi
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

    return ctx


def create_socket():
    ctx = create_context()
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return SSL.Connection(ctx, raw_sock)


def do_handshake(domain):
    sock = create_socket()

    sock.request_ocsp()

    ocsp_response = None

    try:
        sock.connect((domain, 443))
        sock.do_handshake()
        chain = sock.get_peer_cert_chain()
        certificate = sock.get_peer_certificate()

        ctx = sock.get_context()
        if ctx.ocsp_resps:
            ocsp_response = ctx.ocsp_resps[0]

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
