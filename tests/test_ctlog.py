from __future__ import unicode_literals  # for Python-2
import os.path

import pytest

from ctutlz import ctlog


def test_log_dict_from_log_text():
    test_data = [
        {
            'input': '''\
ct.googleapis.com/pilot

Base64 Log ID: pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=
Operator: Google
Contact: google-ct-logs@googlegroups.com
Chrome bug: https://crbug.com/389511
''',
            'expected': {
                'url': 'ct.googleapis.com/pilot/',
                'id_b64_non_calculated': 'pLkJkLQYWBSHuxOizGdwCj'
                                         'w1mAT5G9+443fNDsgN3BA=',
                'operated_by': ['Google'],
                'contact': 'google-ct-logs@googlegroups.com',
                'chrome_bug': 'https://crbug.com/389511',
                'maximum_merge_delay': None,
                'description': None,
                'key': None,
            },
        },
        {
            'input': '''\
ct.googleapis.com/submariner

Base64 Log ID: qJnYeAySkKr0YvMYgMz71SRR6XDQ+/WR73Ww2ZtkVoE=
Operator: Google
Contact: google-ct-logs@googlegroups.com

Note that this log is not trusted by Chrome. It only logs certificates that
chain to roots that are on track for inclusion in browser roots or were
trusted at some previous point. See the announcement blog post.

''',
            'expected': {
                'url': 'ct.googleapis.com/submariner/',
                'id_b64_non_calculated': 'qJnYeAySkKr0YvMYgMz71S'
                                         'RR6XDQ+/WR73Ww2ZtkVoE=',
                'operated_by': ['Google'],
                'contact': 'google-ct-logs@googlegroups.com',
                'notes': 'Note that this log is not '
                         'trusted by Chrome. It only logs certificates that '
                         'chain to roots that are on track for inclusion in '
                         'browser roots or were trusted at some previous '
                         'point. See the announcement blog post.',
                'maximum_merge_delay': None,
                'description': None,
                'key': None,
            },
        },
        {
            'input': '''\
ct.googleapis.com/testtube

Base64 Log ID: sMyD5aX5fWuvfAnMKEkEhyrH6IsTLGNQt8b9JuFsbHc=
Operator: Google
Contact: google-ct-logs@googlegroups.com

Note that this log is intended for testing purposes only and will only log
certificates that chain to a root explicitly added to it.
To add a test root to Testtube, please email google-ct-logs@googlegroups.com

A test root for Testtube should:

  * have a certificate "Subject" field that:
    * includes the word "Test" (to reduce the chances of real certificates being mixed up with test certificates.
    * identifies the organization that the test root is for (to allow easy classification of test traffic).
  * not allow real certificates to chain to it, either because:
    * it is a self-signed root CA certificate identified as a test certificate (as above).
    * it is an intermediate CA certificate that chains to a root certificate that is also identified as a test certificate.
  * be a CA certificate, by:
    * having CA:TRUE in the Basic Constraints extension.
    * include the 'Certificate Sign' bit in the Key Usage extension.

Note that for historical reasons Testtube includes some test roots that do not
comply with all of the above requirements.

''',
            'expected': {
                'url': 'ct.googleapis.com/testtube/',
                'id_b64_non_calculated': 'sMyD5aX5fWuvfAnMKEkEhy'
                                         'rH6IsTLGNQt8b9JuFsbHc=',
                'operated_by': ['Google'],
                'contact': 'google-ct-logs@googlegroups.com',
                'notes': 'Note that this log is intended for testing purposes '
                         'only and will only log certificates that chain to a '
                         'root explicitly added to it. To add a test root to '
                         'Testtube, please email '
                         'google-ct-logs@googlegroups.com '
                         'A test root for Testtube should: '
                         '* have a certificate "Subject" field that: '
                         '* includes the word "Test" (to reduce the chances of '
                         'real certificates being mixed up with test '
                         'certificates. '
                         '* identifies the organization that the test root is '
                         'for (to allow easy classification of test traffic). '
                         '* not allow real certificates to chain to it, either '
                         'because: '
                         '* it is a self-signed root CA certificate identified '
                         'as a test certificate (as above). '
                         '* it is an intermediate CA certificate that chains '
                         'to a root certificate that is also identified as a '
                         'test certificate. '
                         '* be a CA certificate, by: '
                         '* having CA:TRUE in the Basic Constraints extension. '
                         "* include the 'Certificate Sign' bit in the Key "
                         'Usage extension. '
                         'Note that for historical reasons Testtube includes '
                         'some test roots that do not comply with all of the '
                         'above requirements.''',
                'maximum_merge_delay': None,
                'description': None,
                'key': None,
            },
        },
    ]
    for cur_test in test_data:
        got = ctlog._log_dict_from_log_text(log_text=cur_test['input'])
        assert got == cur_test['expected']


# @pytest.mark.skip(reason="no way of currently testing this")
def test_logs_dict_from_html_str():
    thisdir = os.path.abspath(os.path.dirname(__file__))
    test_data = [
        {
            'filename': 'known-logs_2018-02-27.html',
            'expected_logs_dict': {
                'special_purpose_logs': [
                    {
                        'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated':
                            'HQJLjrFJizRN/YfqPvwJlvdQbyNdHUlwYaR3PEOcJfs=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'This log is not trusted by Chrome. It '
                                 'only logs certificates that have expired. '
                                 'See the announcement post.',
                        'operated_by': ['Google'],
                        'url': 'ct.googleapis.com/daedalus/'
                    },
                    {
                        'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated':
                            'qJnYeAySkKr0YvMYgMz71SRR6XDQ+/WR73Ww2ZtkVoE=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'This log is not trusted by Chrome. It '
                                 'only logs certificates that chain to '
                                 'roots that are on track for inclusion in '
                                 'browser roots or were trusted at some '
                                 'previous point. See the announcement blog '
                                 'post.',
                           'operated_by': ['Google'],
                           'url': 'ct.googleapis.com/submariner/'
                    },
                    {
                        'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated':
                            'sMyD5aX5fWuvfAnMKEkEhyrH6IsTLGNQt8b9JuFsbHc=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'This log is intended for testing purposes '
                                 'only and will only log certificates that '
                                 'chain to a root explicitly added to it. '
                                 'To add a test root to Testtube, please '
                                 'email google-ct-logs@googlegroups.com A '
                                 'test root for Testtube should: * have a '
                                 'certificate "Subject" field that: * '
                                 'includes the word "Test" (to reduce the '
                                 'chances of real certificates being mixed '
                                 'up with test certificates. * identifies '
                                 'the organization that the test root is '
                                 'for (to allow easy classification of test '
                                 'traffic). * not allow real certificates '
                                 'to chain to it, either because: * it is a '
                                 'self-signed root CA certificate '
                                 'identified as a test certificate (as '
                                 'above). * it is an intermediate CA '
                                 'certificate that chains to a root '
                                 'certificate that is also identified as a '
                                 'test certificate. * be a CA certificate, '
                                 'by: * having CA:TRUE in the Basic '
                                 'Constraints extension. * include the '
                                 "'Certificate Sign' bit in the Key Usage "
                                 'extension. For historical reasons '
                                 'Testtube includes some test roots that do '
                                 'not comply',
                        'operated_by': ['Google'],
                        'url': 'ct.googleapis.com/testtube/'
                    }
                ]
            }
        },
    ]
    for item in test_data:
        with open(os.path.join(thisdir, 'data', 'test_ctlog',
                               item['filename'])) as fh:
            input = fh.read()

        got = ctlog._logs_dict_from_html(html=input)

        # from pprint import pprint; pprint(got, indent=1, width=80)
        assert got == item['expected_logs_dict']
