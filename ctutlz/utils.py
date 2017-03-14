import base64
import hashlib
import subprocess

from utlz import func_has_arg, namedtuple


def encode_to_pem(arg):
    '''Return arg as PEM encoded string (not as bytes-str).'''
    res = base64.b64encode(arg)
    # assert type(res) == bytes, 'type(result) is ' + str(type(res))
    return res.decode('ascii')


def decode_from_pem(arg):
    return base64.b64decode(arg)


def sha256_digest(arg):
    return hashlib.sha256(arg).digest()


def digest_from_pem(arg):
    return sha256_digest(decode_from_pem(arg))


def digest_from_pem_encoded_to_pem(arg):
    return encode_to_pem(digest_from_pem(arg))


CmdResult = namedtuple(
    typename='CmdResult',
    field_names=[
        'exitcode',
        'stdout',      # type: bytes
        'stdout_str',  # type: str
        'stderr',      # type: bytes
        'stderr_str',  # type: str
        'cmd',
        'input',
    ],
    # FIXME: DEBUG
#    lazy_vals={
#        'stdout_str': lambda self: self.stdout.decode('utf-8'),
#        'stderr_str': lambda self: self.stderr.decode('utf-8'),
#    }
)


# FIXME: utils function (when in-out-err streams generig => general utils func)
def run_cmd(cmd, input=None, timeout=30, max_try=3, num_try=1):
    if type(cmd) == str:
        cmd = cmd.split()
    process = subprocess.Popen(cmd,
                               stdin=open('/dev/null', 'r'),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    communicate_has_timeout = func_has_arg(func=process.communicate,
                                           arg='timeout')
    exception = Exception
    if communicate_has_timeout:
        exception = subprocess.TimeoutExpired  # python 3.x
    stdout = stderr = b''
    exitcode = None
    try:
        if communicate_has_timeout:
            # python 3.x
            stdout, stderr = process.communicate(input, timeout)
            exitcode = process.wait()
        else:
            # python 2.x
            if timeout is None:
                stdout, stderr = process.communicate(input)
                exitcode = process.wait()
            else:
                # thread-recipe: https://stackoverflow.com/a/4825933
                def target():
                    # closure-recipe: https://stackoverflow.com/a/23558809
                    target.out, target.err = process.communicate(input)
                import threading
                thread = threading.Thread(target=target)
                thread.start()
                thread.join(timeout)
                if thread.is_alive():
                    process.terminate()
                    thread.join()
                    exitcode = None
                else:
                    exitcode = process.wait()
                stdout = target.out
                stderr = target.err
    except exception:
        if num_try < max_try:
            return run_cmd(cmd, input, timeout, max_try, num_try+1)
#        pass
        else:
            return CmdResult(exitcode,
                             stdout, stdout.decode('utf-8'),
                             stderr, stderr.decode('utf-8'),
                             cmd, input)
    return CmdResult(exitcode,
                     stdout, stdout.decode('utf-8'),
                     stderr, stderr.decode('utf-8'),
                     cmd, input)


def to_hex(val):
    if type(val) is int:
        return hex(val)
    try:
        # Python-2.x
        if type(val) is long:
            return hex(val)
    except NameError:
        pass
    # else:
    try:
        # Python-2.x
        return ":".join("{0:02x}".format(ord(char)) for char in val)
    except TypeError:
        # Python-3.x
        return ":".join("{0:02x}".format(char) for char in val)
