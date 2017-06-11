# ctutlz

Python utils library and tools for
[Certificate Transparency](https://www.certificate-transparency.org/).

[![Build Status](https://travis-ci.org/theno/ctutlz.svg?branch=master)](https://travis-ci.org/theno/ctutlz)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/ctutlz.svg)](https://pypi.python.org/pypi/ctutlz)
[![PyPI Version](https://img.shields.io/pypi/v/ctutlz.svg)](https://pypi.python.org/pypi/ctutlz)

This is the first implementation in Python which scrapes the SCTs at the TLS
handshake by [certificate extension][1], by [TLS extension][2], and
by [OCSP stapling][3] directly using the OpenSSL C-API (without forking
subprocesses to call any OpenSSL commands).

[1]: https://www.certificate-transparency.org/how-ct-works#TOC-X.509v3-Extension
[2]: https://www.certificate-transparency.org/how-ct-works#TOC-TLS-Extension
[3]: https://www.certificate-transparency.org/how-ct-works#TOC-OCSP-Stapling

## Usage

As a tool:

```
> verify-scts --help

usage: verify-scts [-h] [--short | --debug]
                   [--cert-only | --tls-only | --ocsp-only]
                   [--log-list <filename> | --latest-logs]
                   hostname [hostname ...]

Verify Signed Certificate Timestamps (SCTs) delivered from one or several
hosts by X.509v3 extension, TLS extension, or OCSP stapling

positional arguments:
  hostname              host name of the server (example: 'ritter.vg')

optional arguments:
  -h, --help            show this help message and exit
  --short               show short results and warnings/errors only
  --debug               show more for diagnostic purposes
  --cert-only           only verify SCTs included in the certificate
  --tls-only            only verify SCTs gathered from TLS handshake
  --ocsp-only           only verify SCTs gathered via OCSP request
  --log-list <filename>
                        filename of a log list in JSON format
  --latest-logs         for SCT verification against known CT Logs (compliant
                        with Chome's CT policy) download latest version of
                        https://www.certificate-transparency.org/known-
                        logs/all_logs_list.json -- use built-in log list from
                        2017-06-05 if --latest-logs or --log-list are not set
```

Examples:

    > verify-scts google.com --short

    # google.com

    ## SCTs by Certificate

    no SCTs

    ## SCTs by TLS

    ```
    LogID b64 : pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=
    Sign. b64 : MEUCIGUHno90gGUepkOAkIWf0js56ce7FVnq1sXRM+cW8xdzAiEAzTRcHqxnBTTBceBlniPpc8OmyxJQLK6nQY8VW3bUsZk=
    Log found : Google 'Pilot' log
    Result    : Verified OK
    ```

    ```
    LogID b64 : 3esdK3oNT6Ygi4GtgWhwfi6OnQHVXIiNPRHEzbbsvsw=
    Sign. b64 : MEYCIQDpSgD3XhIQfqmO0IpHIJma/lchgYbT5yLjlVUYDBOspAIhAOjiHIhceJn0zxrfaT36HMDyY55IntNJ0Ur394NJnU8B
    Log found : Symantec log
    Result    : Verified OK
    ```

    ## SCTs by OCSP

    no SCTs


```bash
> verify-scts  ritter.vg  sslanalyzer.comodoca.com  www.db.com
#   has           ⇧                ⇧                  ⇧
# scts by:   TLS-extension   OCSP-extension   certificate (precert)
```

```bash
# nice: convert the markdown formatted output into other formats with pandoc
domain=ritter.vg
fmt=pdf  # {pdf,html,rst,...}
verify-scts $domain 2>&1 | pandoc --from=markdown -o $domain-scts.$fmt
```

Import module in your python code, for example:

```python
> python3.6

>>> from ctutlz.ctlog import download_log_list
>>> from ctutlz.scripts.verify_scts import verify_scts_by_tls
>>> from ctutlz.tls.handshake import do_handshake
>>>
>>> ctlogs = download_log_list()
>>> handshake_res = do_handshake('google.com')
>>> verifications = verify_scts_by_tls(handshake_res, ctlogs)
>>> for ver in verifications:
...   print(f'{ver.verified}: {ver.log.description}')
...
True: Google 'Pilot' log
True: Symantec log
>>>
>>> from ctutlz.rfc6962 import SignedCertificateTimestamp, MerkleTreeLeaf
```

## Installation

Install the latest version of the pypi python package
[ctutlz](https://pypi.python.org/pypi/ctutlz):

```bash
pip install ctutlz
```

## Development

Clone the source code [repository](https://github.com/theno/ctutlz):

```
git clone https://github.com/theno/ctutlz.git
cd ctutlz
```

### Fabfile

The `fabfile.py` contains devel-tasks to be executed with
[Fabric](http://www.fabfile.org/) (maybe you need to
[install](http://www.fabfile.org/installing.html) it):

```
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

    Keyword-Args:
        args: Optional arguments passed to pytest
        py: python version to run the tests against

    Example:

        fab test:args=-s,py=py27
```

At first, set up python versions with [pyenv](https://github.com/pyenv/pyenv)
and virtualenvs for development with
[tox](https://tox.readthedocs.io/en/latest/):
```
fab pythons
fab tox
```
Tox creates virtualenvs of different Python versions (if they not exist
already) and runs the unit tests against each virtualenv.

On Ubuntu 16.04 you must install `libpython-dev` and `libpython3-dev` in order
to make the tests passing for Python-2.7 and Python-3.5:

```bash
sudo apt-get install  libpython-dev  libpython3-dev

# Then, rebuild the non-working Python-2.7 and Python-3.5 virtualenv and
# run the unit tests:
fab tox:'-e py27 -e py35 --recreate'
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
