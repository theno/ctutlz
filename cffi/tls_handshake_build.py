# https://cffi.readthedocs.io/en/latest/overview.html#real-example-api-level-out-of-line

from cffi import FFI


def create_ffibuilder():
    ffibuilder = FFI()

    module_name = 'ctutlz.tls.tls_handshake'

    # c-source code (like *.c files)
    c_source = r'''\
        // passed to the real C compiler
        # include <sys/types.h>
        # include <pwd.h>
    '''

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

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
