[![Build Status](https://travis-ci.org/theno/ctutlz.svg?branch=master)](https://travis-ci.org/theno/ctutlz)

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
# has scts via
#           TLS-extension   OCSP-extension             certificate (precert)
verify-scts  ritter.vg       sslanalyzer.comodoca.com   www.db.com

verify-scts google.com --short

# Module entry points:
python -m ctutlz
python -m ctutlz.verify_scts
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

Run devel-tasks executed with [Fabric](http://docs.fabfile.org):

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

Setup python versions and virtualenvs for development:
```
fab pythons
fab tox
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
