[![Build Status](https://travis-ci.org/theno/ctutlz.svg?branch=master)](https://travis-ci.org/theno/ctutlz)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/ctutlz.svg)](https://pypi.python.org/pypi/ctutlz)
[![PyPI Version](https://img.shields.io/pypi/v/ctutlz.svg)](https://pypi.python.org/pypi/ctutlz)

# ctutlz

Python utils library and tools for certificate transparency.

## Usage

As a tool:

```bash
> verify-scts --help

usage: verify-scts [-h] [--short | --debug]
                   [--cert-only | --tls-only | --ocsp-only]
                   hostname [hostname ...]

positional arguments:
  hostname     host name of the server (example: 'ritter.vg')

optional arguments:
  -h, --help   show this help message and exit
  --short      show short result and warnings/errors only
  --debug      show more for diagnostic purposes
  --cert-only  only validate SCTs included in the certificate
  --tls-only   only validate SCTs gathered from TLS handshake
  --ocsp-only  only validate SCTs gathered via OCSP status request
```

Example:

```bash
> verify-scts google.com --short

# google.com

## scts_by_cert

## scts_by_tls

LogID b64 : 7ku9t3XOYLrhQmkfq+GeZqMPfl+wctiDAMR7iXqo/cs=
Log found : Google 'Rocketeer' log
Result    : Verified OK

LogID b64 : 3esdK3oNT6Ygi4GtgWhwfi6OnQHVXIiNPRHEzbbsvsw=
Log found : Symantec log
Result    : Verified OK

## scts_by_ocsp

```

```bash
> verify-scts  ritter.vg  sslanalyzer.comodoca.com  www.db.com
#   has           ⇧                ⇧                  ⇧
# scts by:   TLS-extension   OCSP-extension   certificate (precert)
```

Import module in your python code, for example:

```python
from ctutlz.rfc6962 import SignedCertificateTimestamp, MerkleTreeLeaf
```

## Installation

Install the latest version of the pypi python package
[ctutlz](https://pypi.python.org/pypi/ctutlz):

```bash
pip install --process-dependency-links  ctutlz
```

## Development

Clone the source code [repository](https://github.com/theno/ctutlz):

```bash
git clone https://github.com/theno/ctutlz.git
cd ctutlz
```

### Fabfile

Run devel-tasks executed with
[Fabric](http://www.fabfile.org/) (you need to
[install](http://www.fabfile.org/installing.html) it):

```bash
> fab -l

Available commands:

    clean    Delete temporary files not under version control.
    pypi     Build package and upload to pypi.
    pythons  Install latest pythons with pyenv.
    test     Run unit tests.
    tox      Run tox.

# Show task details, e.g. for task `test`:
> fab -d test

Run unit tests.

    Args:
        args: Optional arguments passed to pytest
        py: python version to run the tests against

    Example:

        fab test:args=-s,py=py27
```

Setup python versions and virtualenvs for development with
[pyenv](https://github.com/pyenv/pyenv) and
[tox](https://tox.readthedocs.io/en/latest/):
```
fab pythons
fab tox
```

On Ubuntu 16.04 you must install `libpython3-dev` in order to make the tests
passing for Python-3.5:

```bash
sudo apt-get install  libpython3-dev
```

### Devel-Commands

Run unit tests against several pythons with tox (needs pythons defined
in envlist of `tox.ini` to be installed with pyenv):

```bash
python3.6 -m tox

# only against one python version:
python3.6 -m tox -e py27

# rebuild virtual environments:
python3.6 -m tox -r
```

Run unit tests with pytest (uses tox virtualenv, replace `py36` by e.g.
`py27` where applicable):

```bash
PYTHONPATH='.' .tox/py36/bin/python -m pytest

# show output
PYTHONPATH='.' .tox/py36/bin/python -m pytest -s
```

Run tool `verify-scts` from source:

```bash
PYTHONPATH='.' .tox/py36/bin/python  ctutlz/scripts/verify_scts -h
```
