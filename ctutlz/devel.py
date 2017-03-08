'''devel try-outs'''

import binascii
import socket
from pprint import pprint  # TODO DEVEL
import pdb  # TODO DEVEL

from hexdump import hexdump
from utlz import flo

import certifi
import pyasn1_modules.rfc5280
from pyasn1.codec.der.decoder import decode as der_decoder
from pyasn1.codec.der.encoder import encode as der_encoder
from pyasn1.type.univ import OctetString
from OpenSSL import SSL, crypto


def create_context():

    def verify_callback(conn, cert, errnum, depth, ok):
        '''
        Return:
          0 if okay  (like "zero error")
          != 0, else
        '''
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName

        # TODO DEBUG
        print('\n# # # Got certificate: ' + commonname)
        print('cert:')
        print(cert)
        print('errnum:')
        print(errnum)
        print('depth:')
        print(depth)
        print('ok:')
        print(ok)

#            return ok
#            return 0 # TODO DEBUG
        return bool(ok == 1)
#            return True

    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.set_options(SSL.OP_NO_SSLv2)
    ctx.set_options(SSL.OP_NO_SSLv3)
    ctx.set_verify(SSL.VERIFY_PEER, verify_callback)
    ca_filename = certifi.where()
    ctx.load_verify_locations(ca_filename)
    print('ca_filename')  # TODO DEBUG
    print(ca_filename)    # TODO DEBUG
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
    try:
        print('* 54')
        sock.connect((domain, 443))
        print('* 56')
        res = sock.do_handshake()
        print('* 58')

        chain = sock.get_peer_cert_chain()
        print('----- chain: ------')
        pprint(chain)
        certificate = sock.get_peer_certificate()
        print('----- certificate: ------')
        pprint(certificate)
        pprint(certificate._x509)
        protocol_version = sock.get_protocol_version()
        print('----- protocol version: ------')
        pprint(protocol_version)
        cipher = sock.get_cipher_name()
        print('----- cipher: ------')
        pprint(cipher)


        pprint(dir(sock))

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        exc_type = type(exc)
        print(flo('### {exc}\n\n{tb}\n\nexc-type: {exc_type}'))
        raise exc
    finally:
        sock.close()  # sock.close() possible?

    return certificate


def devel():
    cert_spec = pyasn1_modules.rfc5280.Certificate()

    if False:
        pprint(cert_spec.componentType)

    #    cert_x509 = do_handshake('www.google.com')
        cert_x509 = do_handshake('www.db.com')  # Deutsche Bank (EV-Zertifikat)

    #    pprint(crypto.dump_certificate(type=crypto.FILETYPE_PEM, cert=cert_x509))  # as PEM
    #    pprint(crypto.dump_certificate(type=crypto.FILETYPE_ASN1, cert=cert_x509)) # as DER
    #    print(crypto.dump_certificate(type=crypto.FILETYPE_TEXT, cert=cert_x509).decode('ascii'))  # human readable

        cert_der = crypto.dump_certificate(type=crypto.FILETYPE_ASN1,
                                           cert=cert_x509)

        # write cert to file
        with open('www.db.com.crt', 'wb') as fh:
            fh.write(cert_der)
        return
    else:
        # read cert from file
        with open('www.db.com.crt', 'rb') as fhr:
            cert_der = fhr.read()

    print('\n---\n')
    hexdump(cert_der)

    cert_asn1, rest_of_input = der_decoder(cert_der, asn1Spec=cert_spec)

    # FIXME: use pyopenssl access method
    ext_stcs = [extension
                for extension
                in cert_asn1['tbsCertificate']['extensions']
                if str(extension['extnID']) == '1.3.6.1.4.1.11129.2.4.2'][0]

    os_inner_der = ext_stcs['extnValue']  # type: OctetString()
    os_inner, _ = der_decoder(os_inner_der, OctetString())


#    print('\n---\n')
#    hexdump(sct_list_der)

    from ctutlz.sct.scrape.tls_extension_18 import TlsExtension18
    from ctutlz.sct.scrape.tls_extension_18 import SignedCertificateTimestampList

    sctlist_hex = os_inner.prettyPrint().split('0x')[-1]

    print('\n---- os_inner\n')
    print(sctlist_hex)
    print(len(sctlist_hex))
    print(os_inner.prettyPrint())
    print(len(os_inner.prettyPrint()))
    print(dir(os_inner))
    print(os_inner.asOctets())
    print('')
    print(os_inner._value)         # TODO: Bug in pyasn1 ???
    print(os_inner.prettyPrint())  # why prettyPrint() behaves now differently?
    print(os_inner.asNumbers())
    print(len(os_inner.asNumbers()))
    print('\n----\n')

    print('\n---- hexlify Primer\n')
    print(binascii.hexlify(b'adsf'))
    print(binascii.unhexlify(b'61647366'))
    print('\n----\n')

    sctlist_der = binascii.unhexlify(sctlist_hex)

    # does not work, and i understand, why :-)
#    tls_extension_18 = TlsExtension18(sctlist_der)
#    print(tls_extension_18)

    sctlist = SignedCertificateTimestampList(sctlist_der)
    print(sctlist)

    print('\n---- SCT instances\n')
    from ctutlz.sct import Sct
    scts = [Sct(entry.sct_der) for entry in sctlist.sct_list]
    pprint(scts)

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
        print(flo('log_id (PEM): {log.id_pem}'))
        print(flo('description: {log.description}'))


if __name__ == '__main__':
    devel()
