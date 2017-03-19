"""A python utils library

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


description = 'A python utils library'
long_description = create_readme_with_long_description()

setup(
    name='ctutlz',
    version='0.4.0',
    description=description,
    long_description=long_description,
    url='https://github.com/theno/ctutlz',
    author='Theodor Nolte',
    author_email='ctutlz@theno.eu',
    license='MIT',
    entry_points={
        'console_scripts': [
            'verify-scts = ctutlz.verify_scts:main',
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
    install_requires=[
        'utlz',
        'pytz', 'pyasn1', 'ndg-httpsclient',  # for verify-cert
        'pyOpenSSL',
        'asn1ate', 'certifi', 'hexdump',                   # for devel.py
        'pyasn1-modules',
    ],
    dependency_links=[
        #'https://github.com/etingof/pyasn1-modules/tarball/master#egg=pyasn1-modules-0.0.9',
        'git+https://github.com/etingof/pyasn1-modules.git#egg=pyasn1-modules-0.0.9',
        # 16.2.0 has no ocsp support
        # 'git+https://github.com/pyca/pyopenssl.git#egg=pyOpenSSL-16.3.0',
        'git+https://github.com/theno/pyopenssl.git#egg=pyOpenSSL-16.3.0',
    ],
    extras_require={
        'dev': ['pypandoc'],
    },
)
