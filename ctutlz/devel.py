'''devel try-outs'''

import binascii
import socket
from pprint import pprint  # TODO DEVEL
import pdb  # TODO DEVEL

import certifi
import pyasn1_modules.rfc5280
from hexdump import hexdump
from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.type.univ import OctetString
from OpenSSL import SSL, crypto

from utlz import flo

from ctutlz.sct import Sct
from ctutlz.sctlist import SignedCertificateTimestampList


def create_context():

    def verify_callback(conn, cert, errnum, depth, ok):
        '''
        Return:
          0 if okay  (like "zero error")
          != 0, else
        '''
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        return bool(ok == 1)

    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.set_options(SSL.OP_NO_SSLv2)
    ctx.set_options(SSL.OP_NO_SSLv3)

    ctx.set_verify(SSL.VERIFY_PEER, verify_callback)
    ca_filename = certifi.where()
    ctx.load_verify_locations(ca_filename)

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
    # TODO: context in blocking mode
    # TODO: get tls extension
    #       https://github.com/openssl/openssl/blob/master/apps/s_client.c#L1634
    sock = create_socket()

    sock.request_ocsp()

    ocsp_response = None

    try:
        sock.connect((domain, 443))
        res = sock.do_handshake()
        chain = sock.get_peer_cert_chain()
        certificate = sock.get_peer_certificate()
        protocol_version = sock.get_protocol_version()
        cipher = sock.get_cipher_name()

#        from pprint import pprint
#        pprint(dir(sock))  # TODO DEBUG
        ctx = sock.get_context()
#        pprint(ctx.ocsp_res)
        if ctx.ocsp_resps:
            ocsp_response = ctx.ocsp_resps[0]

        # open('ocsp_res', 'wb').write(ocsp_response)

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        exc_type = type(exc)
        print(flo('### {exc}\n\n{tb}\n\nexc-type: {exc_type}'))
        raise exc
    finally:
        sock.close()  # sock.close() possible?

    return certificate, chain, ocsp_response


def devel():
    # if False:
    if True:
        cert_x509, chain_x509s, ocsp_resp_der = do_handshake('www.google.com')
        # Deutsche Bank (EV-Zertifikat)
        cert_x509, chain_x509s, ocsp_resp_der = do_handshake('www.db.com')

        # print(chain_x509s) list of x509 entries

        # pprint(crypto.dump_certificate(type=crypto.FILETYPE_PEM, cert=cert_x509))  # as PEM
        # pprint(crypto.dump_certificate(type=crypto.FILETYPE_ASN1, cert=cert_x509)) # as DER
        # print(crypto.dump_certificate(type=crypto.FILETYPE_TEXT, cert=cert_x509).decode('ascii'))  # human readable

        cert_der = crypto.dump_certificate(type=crypto.FILETYPE_ASN1,
                                           cert=cert_x509)
        # write cert to file
        with open('www.db.com.crt', 'wb') as fh:
            fh.write(cert_der)

        #with open('www.db.com.chain', 'wb') as fh:
        #    for cert in chain_x509s:
        #        fh.write(crypto.dump_certificate(type=crypto.FILETYPE_PEM,
        #                                         cert=cert))
        #for index, cert in enumerate(chain_x509s):
        #    with open(flo('www.db.com.chain_crt_{index}'), 'wb') as fh:
        #        fh.write(crypto.dump_certificate(type=crypto.FILETYPE_PEM,
        #                                         cert=cert))

        # return
    else:
        # read cert from file
        with open('www.db.com.crt', 'rb') as fhr:
            cert_der = fhr.read()

    scts = scts_from_cert(cert_der)
    show_scts(scts)


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


def show_scts(scts):
    for sct in scts:
        print(flo('log_id (PEM): {sct.log_id_pem}'))
        print(flo('version: {sct.version}'))
        print(flo('timestamp: {sct.timestamp}'))
        print(flo('extensions length: {sct.extensions_len_hex}'))
        print(flo('signature alg hash: {sct.signature_alg_hash_hex}'))
        print(flo('signature alg sign: {sct.signature_alg_sign_hex}'))

    print('\n---- known logs (accepted by chrome)\n')
    from ctutlz.log import get_log_list
    logs = get_log_list()
    for log in logs:
        print(flo('description: {log.description}'))
        print(flo('log_id (PEM): {log.id_pem}\n'))


if __name__ == '__main__':
    devel()
