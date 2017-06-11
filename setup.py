"""Certificate Transparency utils library and scripts.

* https://github.com/theno/ctutlz
* https://pypi.python.org/pypi/ctutlz
"""

import os
import shutil
from setuptools import setup, find_packages
from codecs import open


def create_readme_with_long_description():
    this_dir = os.path.abspath(os.path.dirname(__file__))
    readme_md = os.path.join(this_dir, 'README.md')
    readme = os.path.join(this_dir, 'README')
    if os.path.isfile(readme_md):
        if os.path.islink(readme):
            os.remove(readme)
        shutil.copy(readme_md, readme)
    try:
        import pypandoc
        long_description = pypandoc.convert(readme_md, 'rst')
        if os.path.islink(readme):
            os.remove(readme)
        with open(readme, 'w') as out:
            out.write(long_description)
    except(IOError, ImportError, RuntimeError):
        if os.path.isfile(readme_md):
            os.remove(readme)
            os.symlink(readme_md, readme)
        with open(readme, encoding='utf-8') as in_:
            long_description = in_.read()
    return long_description


description = __doc__.split('\n')[0]
long_description = create_readme_with_long_description()

setup(
    name='ctutlz',
    version='0.7.1',
    description=description,
    long_description=long_description,
    url='https://github.com/theno/ctutlz',
    author='Theodor Nolte',
    author_email='ctutlz@theno.eu',
    license='MIT',
    entry_points={
        'console_scripts': [
            'verify-scts = ctutlz.scripts.verify_scts:main',
            'ctlog-get-entries = ctutlz.scripts.ctlog_get_entries:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='python development utilities library '
             'certificate-transparency ct signed-certificate-timestamp sct',
    packages=find_packages(exclude=[
        'contrib',
        'docs',
        'tests',
    ]),
    package_data={'ctutlz': ['all_logs_list.json'], },
    install_requires=[
        'cffi>=1.4.0',
        'pyasn1>=0.2.0',
        'pyasn1-modules>=0.0.9',
        'pyOpenSSL>=17.0.0',
        'requests>=2.17.0',
        'utlz>=0.9.0',
    ],
    extras_require={
        'dev': ['pypandoc'],
    },
    setup_requires=[
        'cffi>=1.4.0'
    ],
    cffi_modules=[
        'ctutlz/tls/handshake_openssl_build.py:ffibuilder'
    ],
)
