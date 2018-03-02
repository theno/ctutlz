import inspect
import sys
from os.path import dirname, join

from fabric.api import execute, local, task
from fabric.context_managers import warn_only, quiet
try:
    from fabsetup.fabutils import extract_minors_from_setup_py, print_msg
    from fabsetup.fabutils import determine_latest_pythons, highest_minor
except ImportError:
    print('fabsetup not installed, run:\n\n    pip2 install fabsetup')
    sys.exit(1)


# inspired by: http://stackoverflow.com/a/6618825
def flo(string):
    '''Return the string given by param formatted with the callers locals.'''
    callers_locals = {}
    frame = inspect.currentframe()
    try:
        outerframe = frame.f_back
        callers_locals = outerframe.f_locals
    finally:
        del frame
    return string.format(**callers_locals)


def _wrap_with(color_code):
    '''Color wrapper.

    Example:
        >>> blue = _wrap_with('34')
        >>> print(blue('text'))
        \033[34mtext\033[0m
    '''
    def inner(text, bold=False):
        '''Inner color function.'''
        code = color_code
        if bold:
            code = flo("1;{code}")
        return flo('\033[{code}m{text}\033[0m')
    return inner


cyan = _wrap_with('36')


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no", or None (which means an answer
    of the user is required).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, '1': True,
             "no": False, "n": False, '0': False, }
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


@task
def clean(deltox=False):
    '''Delete temporary files not under version control.

    Args:
        deltox: If True, delete virtual environments used by tox
    '''

    basedir = dirname(__file__)

    print(cyan('delete temp files and dirs for packaging'))
    local(flo(
        'rm -rf  '
        '{basedir}/.eggs/  '
        '{basedir}/ctutlz.egg-info/  '
        '{basedir}/dist  '
        '{basedir}/README  '
        '{basedir}/build/  '
    ))

    print(cyan('\ndelete temp files and dirs for editing'))
    local(flo(
        'rm -rf  '
        '{basedir}/.cache  '
        '{basedir}/.ropeproject  '
    ))

    print(cyan('\ndelete bytecode compiled versions of the python src'))
    # cf. http://stackoverflow.com/a/30659970
    local(flo('find  {basedir}/ctutlz  {basedir}/tests  ') +
          '\( -name \*pyc -o -name \*.pyo -o -name __pycache__ '
          '-o -name \*.so -o -name \*.o -o -name \*.c \) '
          '-prune '
          '-exec rm -rf {} +')

    if deltox:
        print(cyan('\ndelete tox virual environments'))
        local(flo('cd {basedir}  &&  rm -rf .tox/'))


def _pyenv_exists():
    with quiet():
        res = local('pyenv')
        if res.return_code == 127:
            return False
    return True


def _determine_latest_pythons():
    filename_setup_py = join(dirname(__file__), 'setup.py')
    minors = extract_minors_from_setup_py(filename_setup_py)
    return determine_latest_pythons(minors)


@task
def pythons():
    '''Install latest pythons with pyenv.

    The python version will be activated in the projects base dir.

    Will skip already installed latest python versions.
    '''
    if not _pyenv_exists():
        print('\npyenv is not installed. You can install it with fabsetup '
              '(https://github.com/theno/fabsetup):\n\n    ' +
              cyan('mkdir ~/repos && cd ~/repos\n    '
                   'git clone  https://github.com/theno/fabsetup.git\n    '
                   'cd fabsetup  &&  fab setup.pyenv -H localhost'))
        return 1

    print(cyan('\n## determine latest python versions'))
    latest_pythons = _determine_latest_pythons()

    print(cyan('\n## install latest python versions'))
    for version in latest_pythons:
        local(flo('pyenv install --skip-existing {version}'))

    print(cyan('\n## activate pythons'))
    basedir = dirname(__file__)
    latest_pythons_str = '  '.join(latest_pythons)
    local(flo('cd {basedir}  &&  pyenv local  system  {latest_pythons_str}'))

    highest_python = latest_pythons[-1]
    print(cyan(flo(
        '\n## prepare Python-{highest_python} for testing and packaging')))
    packages_for_testing = 'pytest  tox'
    packages_for_packaging = 'pypandoc  twine'
    local(flo('~/.pyenv/versions/{highest_python}/bin/pip  install --upgrade  '
              'pip  {packages_for_testing}  {packages_for_packaging}'))


def _local_needs_pythons(*args, **kwargs):
    with warn_only():
        res = local(*args, **kwargs)
        print(res)
        if res.return_code == 127:
            print(cyan('missing python version(s), '
                       'run fabric task `pythons`:\n\n    '
                       'fab pythons\n'))
            sys.exit(1)


@task
def tox(args=''):
    '''Run tox.

    Build package and run unit tests against several pythons.

    Args:
        args: Optional arguments passed to tox.
        Example:

            fab tox:'-e py36 -r'
    '''
    basedir = dirname(__file__)

    latest_pythons = _determine_latest_pythons()
    # e.g. highest_minor_python: '3.6'
    highest_minor_python = highest_minor(latest_pythons)

    _local_needs_pythons(flo('cd {basedir}  &&  '
                             'python{highest_minor_python} -m tox {args}'))


@task
def test(args='', py=None):
    '''Run unit tests.

    Keyword-Args:
        args: Optional arguments passed to pytest
        py: python version to run the tests against

    Example:

        fab test:args=-s,py=py27
    '''
    basedir = dirname(__file__)

    if py is None:
        # e.g. envlist: 'envlist = py26,py27,py33,py34,py35,py36'
        envlist = local(flo('cd {basedir}  &&  grep envlist tox.ini'),
                        capture=True)
        _, py = envlist.rsplit(',', 1)

    with warn_only():
        res = local(flo('cd {basedir}  &&  '
                        "PYTHONPATH='.' .tox/{py}/bin/python -m pytest {args}"))
        print(res)
        if res.return_code == 127:
            print(cyan('missing tox virtualenv, '
                       'run fabric task `tox`:\n\n    '
                       'fab tox\n'))
            sys.exit(1)


@task
def pypi():
    '''Build package and upload to pypi.'''
    if query_yes_no('version updated in ctutlz/_version.py?'):

        print(cyan('\n## clean-up\n'))
        execute(clean)

        basedir = dirname(__file__)

        latest_pythons = _determine_latest_pythons()
        # e.g. highest_minor: '3.6'
        highest_minor = highest_minor(latest_pythons)
        python = flo('python{highest_minor}')

        print(cyan('\n## build package'))
        _local_needs_pythons(flo('cd {basedir}  &&  {python}  setup.py  sdist'))

        print(cyan('\n## upload package'))
        local(flo('cd {basedir}  &&  {python} -m twine upload  dist/*'))


@task
def uplogs():
    '''Download latest version for `ctutlz/all_logs_list.json`,
    `ctutlz/log_list.json`, and `ctutlz/log_list_pubkey.pem`.
    '''
    basedir = dirname(__file__)
    for filename in [
            'all_logs_list.json',
            'log_list.json',
            'log_list_pubkey.pem', ]:
        print_msg(flo('\n## {filename}\n'))
        url = flo('https://www.gstatic.com/ct/log_list/{filename}')
        local(flo('wget {url} -O {basedir}/ctutlz/{filename}'))
        local(flo('cd {basedir}  &&  git diff ctutlz/{filename}'))
