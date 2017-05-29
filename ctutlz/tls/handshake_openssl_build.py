# https://cffi.readthedocs.io/en/latest/overview.html#real-example-api-level-out-of-line

# ffi means foreign function interface, cf.
# https://enwikipedia.org/wiki/Foreign_function_interface

from cffi import FFI


def create_ffibuilder():
    module_name = 'ctutlz.tls.handshake_openssl'

    libraries = ['ssl', 'crypto']

    csource_ffi = r'''
        #include "stdio.h"  // FILE

        #include "openssl/bio.h"
        #include "openssl/err.h"
        #include "openssl/ssl.h"
    '''

    cdefinitions_lib = r'''
        typedef struct ssl_ctx_st SSL_CTX;
        typedef struct ssl_st SSL;

        // for TLS extension 18

        typedef int (*custom_ext_add_cb) (SSL *s, unsigned int ext_type,
                                          const unsigned char **out,
                                          size_t *outlen, int *al,
                                          void *add_arg);
        typedef void (*custom_ext_free_cb) (SSL *s, unsigned int ext_type,
                                            const unsigned char *out,
                                            void *add_arg);
        typedef int (*custom_ext_parse_cb) (SSL *s, unsigned int ext_type,
                                            const unsigned char *in,
                                            size_t inlen, int *al,
                                            void *parse_arg);
        int SSL_CTX_add_client_custom_ext(SSL_CTX *ctx, unsigned int ext_type,
                                          custom_ext_add_cb add_cb,
                                          custom_ext_free_cb free_cb,
                                          void *add_arg,
                                          custom_ext_parse_cb parse_cb,
                                          void *parse_arg);

        extern "Python" static int serverinfo_cli_parse_cb(SSL *s,
                                                           unsigned int ext_type,
                                                           const unsigned char *in,
                                                           size_t inlen,
                                                           int *al, void *arg);
    '''

    ffibuilder = FFI()
    ffibuilder.set_source(module_name, csource_ffi, libraries=libraries)
    ffibuilder.cdef(cdefinitions_lib)
    return ffibuilder


# hook for the kwarg 'cffi_modules' of the setup() call in setup.py
ffibuilder = create_ffibuilder()


def compile():
    ffibuilder.compile(verbose=False)
