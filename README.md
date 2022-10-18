---> __[CT Deployment Study](https://theno.github.io/presi-ct-deployment)__ <---

----

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

----
* [Usage](#usage)
  * [verify-scts](#verify-scts)
  * [ctloglist](#ctloglist)
  * [decompose-cert](#decompose-cert)
  * [API](#api)
* [Installation](#installation)
* [Installation and Development 2022-10](#installation-and-development-2022-10)
* [Development](#development)
  * [Fabfile](#fabfile)
  * [Devel-Commands](#devel-commands)
----

## Usage

### verify-scts

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
                        with Chrome's CT policy) download latest version of
                        https://www.gstatic.com/
                        ct/log_list/v2/all_logs_list.json -- use built-in log
                        list really_all_logs.json from 2020-04-05 if --latest-
                        logs or --log-list are not set


```

#### Examples:
##### Simple google.com verification

    > verify-scts google.com --short

    # google.com

    * no EV cert
    * not issued by Let's Encrypt

    ## SCTs by Certificate

    ```
    LogID b64 : sh4FzIuizYogTodm+Su5iiUgZ2va+nDnsklTLe+LkF4=
    Sign. b64 : MEUCIDsJPECetlDd6KUBhpZFsOfhQYoI45i+T9Lod1wsY8gN
                AiEA/ohyB+GuG+Z4MJNxH94xQUUpd2jpiDbG1r6FneDRpkE=
    Log found : Google 'Argon2020' log
    Chrome    : True
    Result    : Verified OK
    ```

    ```
    LogID b64 : Xqdz+d9WwOe1Nkh90EngMnqRmgyEoRIShBh1loFxRVg=
    Sign. b64 : MEUCIQChTO0dZC+zFcuvt3RPvuvMZ7RohbeizyRy5OhMpC/N
                kgIgTUhJTv5zdKBXDCgrgPoIYarBkYmTsirQDhALSEHHmZU=
    Log found : Cloudflare 'Nimbus2020' Log
    Chrome    : True
    Result    : Verified OK
    ```

    ## SCTs by TLS

    no SCTs

    ## SCTs by OCSP

    no SCTs

##### Domains to try for different TLS-features

```bash
> verify-scts  ritter.vg  sslanalyzer.comodoca.com  www.db.com
#   has           ⇧                ⇧                  ⇧
# scts by:   TLS-extension   OCSP-extension   certificate (precert)
```

##### Output markdown into PDF

```bash
# nice: convert the markdown formatted output into other formats with pandoc
domain=ritter.vg
fmt=pdf  # {pdf,html,rst,...}
verify-scts $domain 2>&1 | pandoc --from=markdown -o $domain-scts.$fmt
```

### ctloglist

```
> ctloglist --help

usage: ctloglist [-h] [-v] [--short | --debug] [--json | --schema]

Download, merge and summarize known logs for Certificate Transparency (CT)

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  print version number
  --short        show short results
  --debug        show more for diagnostic purposes
  --json         print merged log lists as json
  --schema       print json schema

Print output to stdout, warning and errors to stderr. Currently there exist
three log lists with differing infos: 1. listing of webpage
https://www.certificate-transparency.org/known-logs 2. log_list.json 3.
all_logs_list.json. This three log lists will be merged into one list in the
future.
```
Discussion:  
https://groups.google.com/forum/?fromgroups#!topic/certificate-transparency/zBv7EK0522w

Created with `ctloglist`:
* [really_all_logs.md](https://github.com/theno/ctutlz/blob/master/ctutlz/really_all_logs.md)
* [really_all_logs.json](https://github.com/theno/ctutlz/blob/master/ctutlz/really_all_logs.json)

Examples:

```bash
# list really all known logs
#  infos aggregated from:
#  * log_list.json
#  * all_logs.json
#  * from log list webpage

# overview
> ctloglist --short

# full, aggregated info
> ctloglist

# write into a json file
> ctloglist --json > really_all_logs.json
```

```bash
# only show inconsistencies of the ct log lists
> ctloglist 1>/dev/null
```

### decompose-cert

```
> decompose-cert --help

usage: decompose-cert [-h] [-v] --cert <filename> [--tbscert <filename>]
                      [--sign-algo <filename>] [--signature <filename>]

Decompose an ASN.1 certificate into its components tbsCertificate in DER
format, signatureAlgorithm in DER format, and signatureValue as bytes
according to https://tools.ietf.org/html/rfc5280#section-4.1

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         print version number
  --tbscert <filename>  write extracted tbsCertificate to this file (DER
                        encoded)
  --sign-algo <filename>
                        write extracted signatureAlgorithm to this file (DER
                        encoded)
  --signature <filename>
                        write extracted signatureValue to this file

required arguments:
  --cert <filename>     Certificate in PEM, Base64, or DER format
```

### API

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

## Installation and Development 2022-10

ctutlz is outdated and needs to be upgraded to use a current version of
OpenSSL.

Till then you can build and run ctutlz with podman and a Dockerfile
using an old Ubuntu 16.04 and OpenSSL 1.0.2g:

```bash
podman build --tag ctutlz .
podman run -it --rm --name ctutlz --volume ./:/ctutlz ctutlz:latest
root@<container-id>:/ctutlz# pip3 install -e .
root@<container-id>:/ctutlz# python3 ctutlz/scripts/verify_scts.py  google.com
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
PYTHONPATH='.' .tox/py36/bin/python  ctutlz/scripts/verify_scts.py -h
```

### Update really_all_logs

```
.tox/py36/bin/ctloglist > ctutlz/really_all_logs.md
.tox/py36/bin/ctloglist --json > ctutlz/really_all_logs.json
```
