from os.path import join, dirname

from fabric.api import task, local
from utlz import flo


@task
def clean():
    '''Delete temporary files not under version control.'''
    basedir = dirname(__file__)
    local(flo('rm -rf  '
              '{basedir}/ctutlz.egg-info/  '
              '{basedir}/dist  '
              '{basedir}/README  '
              '{basedir}/build/'))
