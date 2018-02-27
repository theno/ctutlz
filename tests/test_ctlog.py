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
    with open(
          os.path.join(thisdir, 'data', 'test_ctlog',
                       'known-logs_2017-08-24.html')) as fh:
        input = fh.read()
    expected_logs_dict = {
        'completely_distrusted_by_chrome': [{'chrome_bug': 'https://crbug.com/667663',
                                             'chrome_state': 'distrusted',
                                             'contact': 'certificatetransparency@outlook.com',
                                             'description': None,
                                             'id_b64_non_calculated': '4BJ2KekEllZOPQFHmESYqkj4rbFmAOt5AqHvmQmQYnM=',
                                             'key': None,
                                             'maximum_merge_delay': None,
                                             'notes': 'Included in Chrome since M-58',
                                             'operated_by': ['Beijing PuChuangSiDa '
                                                             'Technology Ltd.'],
                                             'url': 'www.certificatetransparency.cn/ct/'}],
        'disqualified_from_chrome': [{'chrome_bug': 'https://crbug.com/431700',
                                      'chrome_state': 'disqualified',
                                      'contact': 'atecnica@izenpe.net',
                                      'description': None,
                                      'id_b64_non_calculated': 'dGG0oJz7PUHXUVlXWy52SaRFqNJ3CbDMVkpkgrfrQaM=',
                                      'key': None,
                                      'maximum_merge_delay': None,
                                      'operated_by': ['Izenpe'],
                                      'url': 'ct.izenpe.com/'},
                                     {'chrome_bug': 'https://crbug.com/499446',
                                      'chrome_state': 'disqualified',
                                      'contact': 'ctlog-admin@venafi.com',
                                      'description': None,
                                      'id_b64_non_calculated': 'rDua7X+pZ0dXFZ5tfVdWcvnZgQCUHpve/+yhMTt1eC0=',
                                      'key': None,
                                      'maximum_merge_delay': None,
                                      'operated_by': ['Venafi'],
                                      'url': 'ctlog.api.venafi.com/'},
                                     {'chrome_state': 'disqualified',
                                      'contact': 'ian@certly.io',
                                      'description': None,
                                      'id_b64_non_calculated': 'zbUXm3/BwEb+6jETaj+PAC5hgvr4iW/syLL1tatgSQA=',
                                      'key': None,
                                      'maximum_merge_delay': None,
                                      'operated_by': ['Certly'],
                                      'url': 'log.certly.io/'}],
        'frozen_logs': [{'chrome_state': 'frozen',
                         'contact': 'google-ct-logs@googlegroups.com',
                         'description': None,
                         'id_b64_non_calculated': 'aPaY+B9kgr46jO65KB1M/HFRXWeT1ETRCmesu09P+8Q=',
                         'key': None,
                         'maximum_merge_delay': None,
                         'operated_by': ['Google'],
                         'url': 'ct.googleapis.com/aviator/'}],
        'included_in_chrome': [{'chrome_bug': 'https://crbug.com/632753',
                                'chrome_state': 'included',
                                'contact': 'google-ct-logs@googlegroups.com',
                                'description': None,
                                'id_b64_non_calculated': 'KTxRllTIOWW6qlD8WAfUt2+/WHopctykwwz05UVH9Hg=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Google'],
                                'url': 'ct.googleapis.com/icarus/'},
                               {'chrome_bug': 'https://crbug.com/389511',
                                'chrome_state': 'included',
                                'contact': 'google-ct-logs@googlegroups.com',
                                'description': None,
                                'id_b64_non_calculated': 'pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Google'],
                                'url': 'ct.googleapis.com/pilot/'},
                               {'chrome_bug': 'https://crbug.com/431057',
                                'chrome_state': 'included',
                                'contact': 'google-ct-logs@googlegroups.com',
                                'description': None,
                                'id_b64_non_calculated': '7ku9t3XOYLrhQmkfq+GeZqMPfl+wctiDAMR7iXqo/cs=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Google'],
                                'url': 'ct.googleapis.com/rocketeer/'},
                               {'chrome_bug': 'https://crbug.com/632752',
                                'chrome_state': 'included',
                                'contact': 'google-ct-logs@googlegroups.com',
                                'description': None,
                                'id_b64_non_calculated': 'u9nfvB+KcbWTlCOXqpJ7RzhXlQqrUugakJZkNo4e0YU=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Google'],
                                'url': 'ct.googleapis.com/skydiver/'},
                               {'chrome_bug': 'https://crbug.com/611672',
                                'chrome_state': 'included',
                                'contact': 'ct@startssl.com',
                                'description': None,
                                'id_b64_non_calculated': 'NLtq1sPfnAPuqKSZ/3iRSGydXlysktAfe/0bzhnbSO8=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['StartCom'],
                                'url': 'ct.startssl.com/'},
                               {'chrome_bug': 'https://crbug.com/483625',
                                'chrome_state': 'included',
                                'contact': 'DL-ENG-Symantec-CT-Log@symantec.com',
                                'description': None,
                                'id_b64_non_calculated': '3esdK3oNT6Ygi4GtgWhwfi6OnQHVXIiNPRHEzbbsvsw=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Symantec'],
                                'url': 'ct.ws.symantec.com/'},
                               {'chrome_bug': 'https://crbug.com/419255',
                                'chrome_state': 'included',
                                'contact': 'ctops@digicert.com',
                                'description': None,
                                'id_b64_non_calculated': 'VhQGmi/XwuzT9eG9RLI+x0Z2ubyZEVzA75SYVdaJ0N0=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['DigiCert'],
                                'url': 'ct1.digicert-ct.com/log/'},
                               {'chrome_bug': 'https://crbug.com/698094',
                                'chrome_state': 'included',
                                'contact': 'ctops@digicert.com',
                                'description': None,
                                'id_b64_non_calculated': 'h3W/51l8+IxDmV+9827/Vo1HVjb/SrVgwbTq/16ggw8=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'notes': 'Included in Chrome since M-60',
                                'operated_by': ['DigiCert'],
                                'url': 'ct2.digicert-ct.com/log/'},
                               {'chrome_bug': 'https://crbug.com/688510',
                                'chrome_state': 'included',
                                'contact': 'ctlog-admin@venafi.com',
                                'description': None,
                                'id_b64_non_calculated': 'AwGd8/2FppqOvR+sxtqbpz5Gl3T+d/V5/FoIuDKMHWs=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Venafi'],
                                'url': 'ctlog-gen2.api.venafi.com/'},
                               {'chrome_bug': 'https://crbug.com/605415',
                                'chrome_state': 'included',
                                'contact': 'ctlog@wosign.com',
                                'description': None,
                                'id_b64_non_calculated': 'QbLcLonmPOSvG6e7Kb9oxt7m+fHMBH4w3/rjs7olkmM=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'notes': 'Included in Chrome since M-54',
                                'operated_by': ['WoSign'],
                                'url': 'ctlog.wosign.com/'},
                               {'chrome_bug': 'https://crbug.com/583208',
                                'chrome_state': 'included',
                                'contact': 'ctlog-admin@cnnic.cn',
                                'description': None,
                                'id_b64_non_calculated': 'pXesnO11SN2PAltnokEInfhuD0duwgPC7L7bGF8oJjg=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['CNNIC'],
                                'url': 'ctserver.cnnic.cn/'},
                               {'chrome_bug': 'https://crbug.com/703699',
                                'chrome_state': 'included',
                                'contact': 'ctops@comodo.com',
                                'description': None,
                                'id_b64_non_calculated': 'b1N2rDHwMRnYmQCkURX/dxUcEdkCwQApBo2yCJo32RM=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'notes': 'Included in Chrome since M-60',
                                'operated_by': ['Comodo'],
                                'url': 'mammoth.ct.comodo.com/'},
                               {'chrome_bug': 'https://crbug.com/703700',
                                'chrome_state': 'included',
                                'contact': 'ctops@comodo.com',
                                'description': None,
                                'id_b64_non_calculated': 'VYHUwhaQNgFK6gubVzxT8MDkOHhwJQgXL6OqHQcT0ww=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'notes': 'Included in Chrome since M-60',
                                'operated_by': ['Comodo'],
                                'url': 'sabre.ct.comodo.com/'},
                               {'chrome_bug': 'https://crbug.com/692782',
                                'chrome_state': 'included',
                                'contact': 'DL-ENG-Symantec-SIRIUS-CT-Log@symantec.com',
                                'description': None,
                                'id_b64_non_calculated': 'FZcEiNe5l6Bb61JRKt7o0ui0oxZSZBIan6v71fha2T8=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'notes': 'Included in Chrome since M-60',
                                'operated_by': ['Symantec'],
                                'url': 'sirius.ws.symantec.com/'},
                               {'chrome_state': 'included',
                                'contact': 'DL-ENG-Symantec-VEGA-CT-Log@symantec.com',
                                'description': None,
                                'id_b64_non_calculated': 'vHjh38X2PGhGSTNNoQ+hXwl5aSAJwIG08/aRfz7ZuKU=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Symantec'],
                                'url': 'vega.ws.symantec.com/'}],
        'other_logs': [{'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated': 'HQJLjrFJizRN/YfqPvwJlvdQbyNdHUlwYaR3PEOcJfs=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'Note that this log is not trusted by Chrome. It '
                                 'only logs certificates that have expired. See the '
                                 'announcement post.',
                        'operated_by': ['Google'],
                        'url': 'ct.googleapis.com/daedalus/'},
                       {'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated': 'qJnYeAySkKr0YvMYgMz71SRR6XDQ+/WR73Ww2ZtkVoE=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'Note that this log is not trusted by Chrome. It '
                                 'only logs certificates that chain to roots that are '
                                 'on track for inclusion in browser roots or were '
                                 'trusted at some previous point. See the '
                                 'announcement blog post.',
                        'operated_by': ['Google'],
                        'url': 'ct.googleapis.com/submariner/'},
                       {'chrome_state': None,
                        'contact': 'google-ct-logs@googlegroups.com',
                        'description': None,
                        'id_b64_non_calculated': 'sMyD5aX5fWuvfAnMKEkEhyrH6IsTLGNQt8b9JuFsbHc=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'Note that this log is intended for testing purposes '
                                 'only and will only log certificates that chain to a '
                                 'root explicitly added to it. To add a test root to '
                                 'Testtube, please email '
                                 'google-ct-logs@googlegroups.com A test root for '
                                 'Testtube should: * have a certificate "Subject" '
                                 'field that: * includes the word "Test" (to reduce '
                                 'the chances of real certificates being mixed up '
                                 'with test certificates. * identifies the '
                                 'organization that the test root is for (to allow '
                                 'easy classification of test traffic). * not allow '
                                 'real certificates to chain to it, either because: * '
                                 'it is a self-signed root CA certificate identified '
                                 'as a test certificate (as above). * it is an '
                                 'intermediate CA certificate that chains to a root '
                                 'certificate that is also identified as a test '
                                 'certificate. * be a CA certificate, by: * having '
                                 'CA:TRUE in the Basic Constraints extension. * '
                                 "include the 'Certificate Sign' bit in the Key Usage "
                                 'extension. Note that for historical reasons '
                                 'Testtube includes some test roots that do not '
                                 'comply with all of the above requirements.',
                        'operated_by': ['Google'],
                        'url': 'ct.googleapis.com/testtube/'},
                       {'chrome_state': None,
                        'contact': 'roland@letsencrypt.org',
                        'description': None,
                        'id_b64_non_calculated': 'KWr6LVaLyg0uqESVaulyH8Nfo1Xs2plpOq/UWKca790=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'operated_by': ["Let's Encrypt"],
                        'url': 'clicky.ct.letsencrypt.org/'},
                       {'chrome_state': None,
                        'contact': 'filippo@cloudflare.com',
                        'description': None,
                        'id_b64_non_calculated': 'sLeEvIHA3cR1ROiD8FmFu5B30TTYq4iysuUzmAuOUIs=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'operated_by': ['Up In The Air Consulting'],
                        'url': 'ct.filippo.io/behindthesofa/'},
                       {'chrome_state': None,
                        'description': None,
                        'id_b64_non_calculated': 'p85KTmIH4K3e5f2qSx+GdodntdACpV1HMQ5+ZwqV6rI=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': 'Contact:',
                        'operated_by': ['Symantec'],
                        'url': 'deneb.ws.symantec.com/'},
                       {'chrome_state': None,
                        'contact': 'rob.stradling@comodo.com',
                        'description': None,
                        'id_b64_non_calculated': '23b9raxl59CVCIhuIVm9i5A1L1/q0+PcXiLrNQrMe5g=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'operated_by': ['Comodo'],
                        'url': 'dodo.ct.comodo.com/'},
                       {'chrome_state': None,
                        'contact': 'linus@nordu.net',
                        'description': None,
                        'id_b64_non_calculated': 'U3tpo1ZDNanASQTjlZOywpjrjXpugwI2NcYnJIzWtEA=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'operated_by': ['NORDUnet'],
                        'url': 'flimsy.ct.nordu.net:8080/'},
                       {'chrome_state': None,
                        'contact': 'linus@nordu.net',
                        'description': None,
                        'id_b64_non_calculated': 'qucLfzy41WbIbC8Wl5yfRF9pqw60U1WJsvd6AwEE880=',
                        'key': None,
                        'maximum_merge_delay': None,
                        'notes': '--- Comments',
                        'operated_by': ['NORDUnet'],
                        'url': 'plausible.ct.nordu.net/'}],
        'pending_inclusion_in_chrome': [{'certificate_expiry_range': '[2017-01-01 '
                                                                     '00:00:00 UTC, '
                                                                     '2018-01-01 '
                                                                     '00:00:00 UTC)',
                                         'chrome_bug': 'https://crbug.com/756813',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'google-ct-logs@googlegroups.com',
                                         'description': None,
                                         'id_b64_non_calculated': '+tTJfMSe4vishcXqXOoJ0CINu/TknGtQZi/4aPhrjCg=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['Google'],
                                         'url': 'ct.googleapis.com/logs/argon2017/'},
                                        {'certificate_expiry_range': '[2018-01-01 '
                                                                     '00:00:00 UTC, '
                                                                     '2019-01-01 '
                                                                     '00:00:00 UTC)',
                                         'chrome_bug': 'https://crbug.com/756814',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'google-ct-logs@googlegroups.com',
                                         'description': None,
                                         'id_b64_non_calculated': 'pFASaQVaFVReYhGrN7wQP2KuVXakXksXFEU+GyIQaiU=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['Google'],
                                         'url': 'ct.googleapis.com/logs/argon2018/'},
                                        {'certificate_expiry_range': '[2019-01-01 '
                                                                     '00:00:00 UTC, '
                                                                     '2020-01-01 '
                                                                     '00:00:00 UTC)',
                                         'chrome_bug': 'https://crbug.com/756817',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'google-ct-logs@googlegroups.com',
                                         'description': None,
                                         'id_b64_non_calculated': 'Y/Lbzeg7zCzPC3KEJ1drM6SNYXePvXWmOLHHaFRL2I0=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['Google'],
                                         'url': 'ct.googleapis.com/logs/argon2019/'},
                                        {'certificate_expiry_range': '[2020-01-01 '
                                                                     '00:00:00 UTC, '
                                                                     '2021-01-01 '
                                                                     '00:00:00 UTC)',
                                         'chrome_bug': 'https://crbug.com/756818',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'google-ct-logs@googlegroups.com',
                                         'description': None,
                                         'id_b64_non_calculated': 'sh4FzIuizYogTodm+Su5iiUgZ2va+nDnsklTLe+LkF4=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['Google'],
                                         'url': 'ct.googleapis.com/logs/argon2020/'},
                                        {'certificate_expiry_range': '[2021-01-01 '
                                                                     '00:00:00 UTC, '
                                                                     '2022-01-01 '
                                                                     '00:00:00 UTC)',
                                         'chrome_bug': 'https://crbug.com/756819',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'google-ct-logs@googlegroups.com',
                                         'description': None,
                                         'id_b64_non_calculated': '9lyUL9F3MCIUVBgIMJRWjuNNExkzv98MLyALzE7xZOM=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['Google'],
                                         'url': 'ct.googleapis.com/logs/argon2021/'},
                                        {'chrome_bug': 'http://crbug.com/712069',
                                         'chrome_state': 'pending for inclusion',
                                         'contact': 'CTLS@sheca.com',
                                         'description': None,
                                         'id_b64_non_calculated': 'MtxZwtTEGWjVbhS8YayPDkXbOfrzwVWqQlL1AB+gxiM=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['SHECA'],
                                         'url': 'ct.sheca.com/'},
                                        {'chrome_state': 'pending for inclusion',
                                         'contact': 'ctlog@wosign.com',
                                         'description': None,
                                         'id_b64_non_calculated': 'Y9AAYCbd4QuwYB9FJEaWXuK26izU+8layGalUK+Qdbc=',
                                         'key': None,
                                         'maximum_merge_delay': None,
                                         'operated_by': ['WoSign'],
                                         'url': 'ctlog2.wosign.com/'}],
        'rejected_by_chrome': [{'chrome_bug': 'http://crbug.com/403190',
                                'chrome_state': 'rejected',
                                'contact': 'ops@ctlogs.org',
                                'description': None,
                                'id_b64_non_calculated': 'OTdvVF97Rgf1l0LXaM1dJDe/NHO2U0pINLz3Lmgcg8k=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Matt Palmer'],
                                'url': 'alpha.ctlogs.org/'},
                               {'chrome_bug': 'http://crbug.com/447603',
                                'chrome_state': 'rejected',
                                'contact': 'ct-help@akamai.com',
                                'description': None,
                                'id_b64_non_calculated': 'lgbALGkAM6odFF9ZxuJkjQVJ8N+WqrjbkVpw2OzzkKU=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Akamai'],
                                'url': 'ct.akamai.com/'},
                               {'chrome_bug': 'https://crbug.com/598526',
                                'chrome_state': 'rejected',
                                'contact': 'capoc@gdca.com.cn',
                                'description': None,
                                'id_b64_non_calculated': 'yc+JCiEQnGZswXo+0GXJMNDgE1qf66ha8UIQuAckIao=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Wang Shengnan'],
                                'url': 'ct.gdca.com.cn/'},
                               {'chrome_bug': 'https://crbug.com/614323',
                                'chrome_state': 'rejected',
                                'contact': 'atecnica@izenpe.eus',
                                'description': None,
                                'id_b64_non_calculated': 'iUFEnHB0Lga5/JznsRa6ACSqNtWa9E8CBEBPAPfqhWY=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['Izenpe'],
                                'url': 'ct.izenpe.eus/'},
                               {'chrome_bug': 'https://crbug.com/534745',
                                'chrome_state': 'rejected',
                                'contact': 'ctlog@wosign.com',
                                'description': None,
                                'id_b64_non_calculated': 'nk/3PcPOIgtpIXyJnkaAdqv414Y21cz8haMadWKLqIs=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['WoSign'],
                                'url': 'ct.wosign.com/'},
                               {'chrome_bug': 'https://crbug.com/654306',
                                'chrome_state': 'rejected',
                                'contact': 'capoc@gdca.com.cn',
                                'description': None,
                                'id_b64_non_calculated': 'kkow+Qkzb/Q11pk6EKx1osZBco5/wtZZrmGI/61AzgE=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['GDCA'],
                                'url': 'ctlog.gdca.com.cn/'},
                               {'chrome_state': 'rejected',
                                'contact': 'CTLS@sheca.com',
                                'description': None,
                                'id_b64_non_calculated': 'z1XiiSNJfDQNUgbQU1Ouslg0tS8fjclSaAnyEu/dfKY=',
                                'key': None,
                                'maximum_merge_delay': None,
                                'operated_by': ['SHECA'],
                                'url': 'ctlog.sheca.com/'}]}

    got = ctlog._logs_dict_from_html(html=input)
    # from pprint import pprint; pprint(got, indent=1, width=80)
    assert got == expected_logs_dict
