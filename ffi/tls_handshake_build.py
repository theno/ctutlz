# https://cffi.readthedocs.io/en/latest/overview.html#real-example-api-level-out-of-line

# ffi means foreign function interface, cf.
# https://enwikipedia.org/wiki/Foreign_function_interface

from cffi import FFI

from ffi.tls_handshake_c_source import c_source


def create_ffibuilder():
    ffibuilder = FFI()

    module_name = 'ctutlz.tls.tls_handshake'

    ffibuilder.set_source(module_name, c_source, libraries=[])

    # definitions: function declaration, types, macros, global variables
    # (like *.h files)
    c_defs = '''\
        // some declarations from the man page

        struct passwd {
            char *pw_name;
            ...;  // literally dot-dot-dot
        };

        struct passwd *getpwuid(int uid);
    '''

    ffibuilder.cdef(c_defs)

    return ffibuilder


# hook for the kwarg 'cffi_modules' of the setup() call in setup.py
ffibuilder = create_ffibuilder()

# if __name__ == '__main__':
#     ffibuilder.compile(verbose=True)
