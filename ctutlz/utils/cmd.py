import subprocess

from utlz import func_has_arg, namedtuple


CmdResult = namedtuple(
    typename='CmdResult',
    field_names=[
        'exitcode',
        'stdout',  # type: bytes
        'stderr',  # type: bytes
        'cmd',
        'input',
    ],
    lazy_vals={
        'stdout_str': lambda self: self.stdout.decode('utf-8'),
        'stderr_str': lambda self: self.stderr.decode('utf-8'),
    }
)


def run_cmd(cmd, input=None, timeout=30, max_try=3, num_try=1):
    '''Run command `cmd`.

    It's like that, and that's the way it is.
    '''
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
        else:
            return CmdResult(exitcode, stdout, stderr, cmd, input)
    return CmdResult(exitcode, stdout, stderr, cmd, input)
