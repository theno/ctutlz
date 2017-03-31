import sys
from os.path import dirname

from fabric.api import execute, local, task
from fabric.context_managers import warn_only, quiet
from utlz import flo, cyan, query_yes_no


@task
def clean(deltox=False):
    '''Delete temporary files not under version control.

    Args:
        deltox: If True, delete virutal environments used by tox
    '''

    basedir = dirname(__file__)

    print(cyan('delete temp files and dirs for packaging'))
    local(flo(
        'rm -rf  '
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
          '\( -name \*pyc -o -name \*.pyo -o -name __pycache__ \) '
          '-prune '
          '-exec rm -rf {} +')

    if deltox:
        print(cyan('\ndelete tox virual environments'))
        local(flo('cd {basedir}  &&  rm -rf .tox/'))


def _pyenv_exists():
    with quiet():
        res = local('pyenv', capture=True)
        if res.return_code == 127:
            return False
    return True


def _determine_latest_pythons():
    # TODO implementation
    return ['2.6.9', '2.7.13', '3.3.6', '3.4.6', '3.5.3', '3.6.1']


def _highest_minor(pythons):
    highest = pythons[-1]
    major, minor, patch = highest.split('.', 2)
    return flo('{major}.{minor}')


@task
def pythons():
    '''Install latest pythons with pyenv.

    The python version will be activated in the projects base dir.

    Will skip already installed latest python versions.
    '''
    if not _pyenv_exists():
        print('\npyenv not installed. install it with fabsetup '
              '(https://github.com/theno/fabsetup):\n\n    ' +
              cyan('fab setup.pyenv -H localhost'))
        return 1

    latest_pythons = _determine_latest_pythons()

    print(cyan('\n## install latest python versions'))
    for version in latest_pythons:
        local(flo('pyenv install --skip-existing {version}'))

    print(cyan('\n## activate pythons'))
    basedir = dirname(__file__)
    latest_pythons_str = '  '.join(latest_pythons)
    local(flo('cd {basedir}  &&  pyenv local  system  {latest_pythons_str}'))

    print(cyan('\n## prepare for testing and packaging'))
    highest_python = latest_pythons[-1]
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
    highest_minor_python = _highest_minor(latest_pythons)

    _local_needs_pythons(flo('cd {basedir}  &&  '
                             'python{highest_minor_python} -m tox {args}'),
                         capture=True)


@task
def test(args='', py=None):
    '''Run unit tests.

    Args:
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
                        "PYTHONPATH='.' .tox/{py}/bin/python -m pytest {args}"),
                    capture=True)
        print(res)
        if res.return_code == 127:
            print(cyan('missing tox virtualenv, '
                       'run fabric task `tox`:\n\n    '
                       'fab tox\n'))
            sys.exit(1)


@task
def pypi():
    '''Build package and upload to pypi.'''
    if query_yes_no('version updated in setup.py?'):

        print(cyan('\n## clean-up\n'))
        execute(clean)

        basedir = dirname(__file__)

        latest_pythons = _determine_latest_pythons()
        # e.g. highest_minor: '3.6'
        highest_minor = _highest_minor(latest_pythons)
        python = flo('python{highest_minor}')

        print(cyan('\n## build package'))
        _local_needs_pythons(flo('cd {basedir}  &&  {python}  setup.py  sdist'))

        print(cyan('\n## upload package'))
        local(flo('cd {basedir}  &&  {python} -m twine upload  dist/*'))
