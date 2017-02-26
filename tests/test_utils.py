import utlz

import ctutlz.utils


def test_run_cmd():
    Input = utlz.namedtuple('Input',
                            'cmd, timeout=30, max_try=3, num_try=1')

    def Expected(exitcode, stdout, stderr):
        return ctutlz.utils.CmdResult(exitcode,
                                      stdout, stdout.decode('utf-8'),
                                      stderr, stderr.decode('utf-8'),
                                      None, None)

    TestCase = utlz.namedtuple('TestDatum', 'comment, input, expected')

    test_data = [
        TestCase(
            'command as string',
            Input(cmd='echo foo'),
            Expected(0, b'foo\n', b'')
        ),
        TestCase(
            'command as list',
            Input(cmd=['echo', 'foo']),
            Expected(0, b'foo\n', b'')
        ),
        TestCase(
            'exitcode != 0',
            Input(cmd=['bash', '-c', 'exit 123']),
            Expected(123, b'', b'')
        ),
        TestCase(
            'on timeout (no return of cmd => exitcode must be None)',
            Input('sleep 0.1', timeout=0.01, max_try=1),
            Expected(None, b'', b'')
        ),
        TestCase(
            'no timeout',
            Input('sleep 0.01', timeout=0.1, max_try=1),
            Expected(0, b'', b'')
        ),
    ]
    for test in test_data:
        res = ctutlz.utils.run_cmd(**test.input._asdict())
        assert res.stdout == test.expected.stdout
        assert res.stderr == test.expected.stderr
        assert res.exitcode == test.expected.exitcode
