from os.path import dirname

from fabric.api import task, local
from utlz import flo, cyan


@task
def clean():
    '''Delete temporary files not under version control.'''

    print(cyan('delete temp files and dirs for packaging'))
    basedir = dirname(__file__)
    local(flo(
        'rm -rf  '
        '{basedir}/ctutlz.egg-info/  '
        '{basedir}/dist  '
        '{basedir}/README  '
        '{basedir}/build/  '
    ))

    print(cyan('delete temp files and dirs for editing'))
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
