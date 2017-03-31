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

Import module in your python code:

```python
import ctutlz
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
```

### fabfile

The devel-commands of the next section can be automatically executed with
[Fabric](docs.fabfile.org):

```bash
> fab -l

Available commands:

    clean    Delete temporary files not under version control.
    pypi     Build package and upload to pypi.
    pythons  Install latest pythons with pyenv.
    test     Run unit tests.
    tox      Run tox.
```

Show task details, e.g. for task `test`:

```bash
> fab -d test

Run unit tests.

    Args:
        args: Optional arguments passed to pytest
        py: python version to run the tests against

    Example:

        fab test:args=-s,py=py27
```

### Devel-Commands

Run unit tests with pytest

```bash
pip install --user  pytest  utlz
PYTHONPATH="."  python -m pytest
```

Run unit tests against several pythons with tox:

```bash
# install tox
pip install tox

# install and activate different python versions
fab setup.pyenv -H localhost
pyenv install  2.6.9
pyenv install  2.7.13
pyenv install  3.3.6
pyenv install  3.4.6
pyenv install  3.5.3
pyenv install  3.6.1
pyenv local  system  2.6.9  2.7.13  3.3.6  3.4.6  3.5.3  3.6.1

# build and run tests
python -m tox
```

Build and publish package:
```bash
# install pypandoc and twine
pip install  pypandoc  twine

# build package
python setup.py sdist

# upload to pypi.org
twine  upload  dist/ctutlz-<VERSION>.tar.gz


# useful oneliners
rm -rf .tox/; python3.6 -m tox
rm -rf dist/; python3.6 setup.py sdist; ls -hal dist/
python3.6 -m twine  upload  dist/ctutlz*
```
