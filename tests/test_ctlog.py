from __future__ import unicode_literals  # for Python-2
import os.path

from ctutlz import ctlog


def test_log_dict_from_log_text():
    test_data = [
        {
            'input': '''\
ct.googleapis.com/pilot

Base64 Log ID: pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=
Operator: Google
Started: 2013-03-25
HTTPS supported: yes

Maximum Merge Delay: 24 hours
Contact: google-ct-logs@googlegroups.com
Chrome inclusion status: Included.
''',
            'expected': {
                'url': 'ct.googleapis.com/pilot/',
                'id_b64_non_calculated': 'pLkJkLQYWBSHuxOizGdwCj'
                                         'w1mAT5G9+443fNDsgN3BA=',
                'operated_by': ['Google'],
                'started': '2013-03-25',
                'https_supported': 'yes',
                'maximum_merge_delay': 86400,
                'contact': 'google-ct-logs@googlegroups.com',
                'chrome_inclusion_status': 'Included.',
                'chrome_status': 'included',
                'description': None,
                'key': None,
            },
        },
        {
            'input': '''\
ct.googleapis.com/submariner - Log for untrusted roots.

Note that this log is not trusted by Chrome. It only logs certificates that
chain to roots that are on track for inclusion in browser roots or were
trusted at some previous point. See the announcement blog post.
Base64 Log ID: qJnYeAySkKr0YvMYgMz71SRR6XDQ+/WR73Ww2ZtkVoE=
Operator: Google
Started: 2016-03-22
HTTPS supported:yes
Contact: google-ct-logs@googlegroups.com
Chrome inclusion status: Not included
''',
            'expected': {
                'url': 'ct.googleapis.com/submariner/',
                'id_b64_non_calculated': 'qJnYeAySkKr0YvMYgMz71S'
                                         'RR6XDQ+/WR73Ww2ZtkVoE=',
                'operated_by': ['Google'],
                'started': '2016-03-22',
                'https_supported': 'yes',
                'contact': 'google-ct-logs@googlegroups.com',
                'chrome_inclusion_status': 'Not included',
                'notes': 'Log for untrusted roots. Note that this log is not '
                         'trusted by Chrome. It only logs certificates that '
                         'chain to roots that are on track for inclusion in '
                         'browser roots or were trusted at some previous '
                         'point. See the announcement blog post.',
                'maximum_merge_delay': None,
                'chrome_status': 'not included',
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
          os.path.join(thisdir, 'data', 'test_ctlog', 'known-logs.html')) as fh:
        input = fh.read()
    expected_logs_dict = {
        'active_logs': [
            {'chrome_inclusion_status': 'Included.',
             'chrome_status': 'included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'pLkJkLQYWBSHuxOizGdwCj'
                                      'w1mAT5G9+443fNDsgN3BA=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Google'],
             'started': '2013-03-25',
             'url': 'ct.googleapis.com/pilot/'},
            {'chrome_inclusion_status': 'Included (since M55).',
             'chrome_status': 'included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'KTxRllTIOWW6qlD8WAfUt2'
                                      '+/WHopctykwwz05UVH9Hg=',
             'key': None,
             'maximum_merge_delay': 86400,
             'notes': "Accepts only certificates issued by Let's Encrypt "
                      'or other subordinate',
             'operated_by': ['Google'],
             'started': '2016-07-27',
             'url': 'ct.googleapis.com/icarus/'},
            {'chrome_inclusion_status': 'Included (since M43).',
             'chrome_status': 'included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': '7ku9t3XOYLrhQmkfq+GeZq'
                                      'MPfl+wctiDAMR7iXqo/cs=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Google'],
             'started': '2014-09-01',
             'url': 'ct.googleapis.com/rocketeer/'},
            {'chrome_inclusion_status': 'Included (since M55).',
             'chrome_status': 'included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'u9nfvB+KcbWTlCOXqpJ7Rz'
                                      'hXlQqrUugakJZkNo4e0YU=',
             'key': None,
             'maximum_merge_delay': 86400,
             'notes': "Does not accept certificates issued by Let's "
                      'Encrypt or other',
             'operated_by': ['Google'],
             'started': '2016-06-10',
             'url': 'ct.googleapis.com/skydiver/'},
            {'chrome_inclusion_status': 'Included.',
             'chrome_status': 'included',
             'contact': 'ctops@digicert.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'VhQGmi/XwuzT9eG9RLI+x0'
                                      'Z2ubyZEVzA75SYVdaJ0N0=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['DigiCert'],
             'submitted_for_inclusion_in_chrome': '2014-09-30',
             'url': 'ct1.digicert-ct.com/log/'},
            {'chrome_inclusion_status': 'Included (since M45).',
             'chrome_status': 'included',
             'contact': 'DL-ENG-Symantec-CT-Log@symantec.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': '3esdK3oNT6Ygi4GtgWhwfi'
                                      '6OnQHVXIiNPRHEzbbsvsw=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Symantec'],
             'submitted_for_inclusion_in_chrome': '2015-05-1',
             'url': 'ct.ws.symantec.com/'},
            {'chrome_inclusion_status': 'Included (since M50).',
             'chrome_status': 'included',
             'contact': 'DL-ENG-Symantec-VEGA-CT-Log@symantec.com; +1 '
                        '(650) 527-466',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'vHjh38X2PGhGSTNNoQ+hXw'
                                      'l5aSAJwIG08/aRfz7ZuKU=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Symantec'],
             'submitted_for_inclusion_in_chrome': '2015-11-13',
             'url': 'vega.ws.symantec.com/'},
            {'chrome_inclusion_status': 'Included (since M47).',
             'chrome_status': 'included',
             'contact': 'ctlog-admin@venafi.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'rDua7X+pZ0dXFZ5tfVdWcv'
                                      'nZgQCUHpve/+yhMTt1eC0=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Venafi'],
             'submitted_for_inclusion_in_chrome': '2015-06-11',
             'url': 'ctlog.api.venafi.com/'},
            {'chrome_inclusion_status': 'Included (since M54).',
             'chrome_status': 'included',
             'contact': 'ctlog@wosign.com; +86-755-8600 8688',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'QbLcLonmPOSvG6e7Kb9oxt'
                                      '7m+fHMBH4w3/rjs7olkmM=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['WoSign'],
             'submitted_for_inclusion_in_chrome': '2016-04-19',
             'url': 'ctlog.wosign.com/'},
            {'chrome_inclusion_status': 'Pending inclusion.',
             'chrome_status': 'pending for inclusion',
             'contact': 'ctlog@wosign.com; +86-755-8600 8688',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'Y9AAYCbd4QuwYB9FJEaWXu'
                                      'K26izU+8layGalUK+Qdbc=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['WoSign'],
             'submitted_for_inclusion_in_chrome': '2017-05-03',
             'url': 'ctlog2.wosign.com/'},
            {'chrome_inclusion_status': 'Included (since M53).',
             'chrome_status': 'included',
             'contact': 'ctlog-admin@cnnic.cn; +86 (010) 58813200',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'pXesnO11SN2PAltnokEInf'
                                      'huD0duwgPC7L7bGF8oJjg=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['CNNIC'],
             'submitted_for_inclusion_in_chrome': '2016-02-02',
             'url': 'ctserver.cnnic.cn/'},
            {'chrome_inclusion_status': 'Included (since M54).',
             'chrome_status': 'included',
             'contact': 'ct@startssl.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'NLtq1sPfnAPuqKSZ/3iRSG'
                                      'ydXlysktAfe/0bzhnbSO8=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['StartCom'],
             'submitted_for_inclusion_in_chrome': '2016-05-13',
             'url': 'ct.startssl.com/'},
            {'chrome_inclusion_status': 'Applied for inclusion but did '
                                        'not qualify.',
             'contact': 'atecnica@izenpe.net',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'iUFEnHB0Lga5/JznsRa6AC'
                                      'SqNtWa9E8CBEBPAPfqhWY=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Izenpe'],
             'submitted_for_inclusion_in_chrome': '2016-05-24',
             'url': 'ct.izenpe.eus/'},
            {'chrome_inclusion_status': 'Applied for inclusion but did '
                                        'not qualify.',
             'contact': 'capoc@gdca.com.cn; +86 (20) 83487228-805',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'yc+JCiEQnGZswXo+0GXJMN'
                                      'DgE1qf66ha8UIQuAckIao=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Wang Shengnan'],
             'submitted_for_inclusion_in_chrome': '2016-04-07',
             'url': 'ct.gdca.com.cn/'},
            {'chrome_inclusion_status': 'Applied for inclusion but did '
                                        'not qualify.',
             'contact': 'capoc@gdca.com.cn; +86 (20) 83487228-805',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'kkow+Qkzb/Q11pk6EKx1os'
                                      'ZBco5/wtZZrmGI/61AzgE=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['GDCA'],
             'submitted_for_inclusion_in_chrome': '2016-10-10',
             'url': 'ctlog.gdca.com.cn/'},
            {'chrome_inclusion_status': 'Pending inclusion.',
             'chrome_status': 'pending for inclusion',
             'contact': 'ctlog-admin@venafi.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'AwGd8/2FppqOvR+sxtqbpz'
                                      '5Gl3T+d/V5/FoIuDKMHWs=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Venafi'],
             'submitted_for_inclusion_in_chrome': '2017-02-03',
             'url': 'ctlog-gen2.api.venafi.com/'},
            {'chrome_inclusion_status': 'Included (since M60).',
             'chrome_status': 'included',
             'contact': 'DL-ENG-Symantec-SIRIUS-CT-Log@symantec.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'ZcEiNe5l6Bb61JRKt7o0u'
                                      'i0oxZSZBIan6v71fha2T8=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Symantec'],
             'submitted_for_inclusion_in_chrome': '2017-02-15',
             'url': 'sirius.ws.symantec.com/'},
            {'chrome_inclusion_status': 'Included (since M60).',
             'chrome_status': 'included',
             'contact': 'ctops@digicert.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'h3W/51l8+IxDmV+9827/Vo'
                                      '1HVjb/SrVgwbTq/16ggw8=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['DigiCert'],
             'submitted_for_inclusion_in_chrome': '2017-03-03',
             'url': 'ct2.digicert-ct.com/log/'},
            {'chrome_inclusion_status': 'Included (since M60).',
             'chrome_status': 'included',
             'contact': 'ctops@comodo.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'b1N2rDHwMRnYmQCkURX/dx'
                                      'UcEdkCwQApBo2yCJo32RM=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Comodo'],
             'submitted_for_inclusion_in_chrome': '2017-03-21',
             'url': 'mammoth.ct.comodo.com/'},
            {'contact': 'ctops@comodo.com',
             'description': None,
             'function': 'active',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'VYHUwhaQNgFK6gubVzxT8M'
                                      'DkOHhwJQgXL6OqHQcT0ww=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Comodo'],
             'submitted_for_inclusion_in_chrome': '2017-03-21',
             'url': 'sabre.ct.comodo.com/'}],
        'frozen_logs': [
            {'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'frozen',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'aPaY+B9kgr46jO65KB1M/H'
                                      'FRXWeT1ETRCmesu09P+8Q=',
             'key': None,
             'maximum_merge_delay': None,
             'operated_by': ['Google'],
             'started': '2013-09-30',
             'url': 'ct.googleapis.com/aviator/'}],
        'logs_that_ceased_operation': [
            {'chrome_inclusion_status': 'Not included anymore (was '
                                        'briefly planned for',
             'chrome_status': 'not included',
             'contact': 'ops@ctlogs.org',
             'description': None,
             'function': 'ceased operation',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'OTdvVF97Rgf1l0LXaM1dJD'
                                      'e/NHO2U0pINLz3Lmgcg8k=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Matt Palmer'],
             'submitted_for_inclusion_in_chrome': '2014-08-12',
             'url': 'alpha.ctlogs.org/'},
            {'chrome_inclusion_status': 'Applied for '
                                        'inclusion but did '
                                        'not qualify.',
             'contact': 'ctlog@wosign.com; +86-755-8600 '
                        '8688',
             'description': None,
             'function': 'ceased operation',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'nk/3PcPOIgtpIXyJnkaAdq'
                                      'v414Y21cz8haMadWKLqIs=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['WoSign'],
             'submitted_for_inclusion_in_chrome': '2015-09-22',
             'url': 'ct.wosign.com/'},
            {'chrome_inclusion_status': 'Included (since '
                                        'M43) but '
                                        'disqualified '
                                        '(since M52).',
             'chrome_status': 'included, but then '
                              'disqualified',
             'contact': 'ian@certly.io',
             'description': None,
             'function': 'ceased operation',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'zbUXm3/BwEb+6jETaj+PAC'
                                      '5hgvr4iW/syLL1tatgSQA=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Certly'],
             'submitted_for_inclusion_in_chrome': '2014-12-14',
             'url': 'log.certly.io/'},
            {'chrome_inclusion_status': 'Included (since '
                                        'M44) but '
                                        'disqualified '
                                        '(since M53).',
             'chrome_status': 'included, but then '
                              'disqualified',
             'contact': 'atecnica@izenpe.net',
             'description': None,
             'function': 'ceased operation',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'dGG0oJz7PUHXUVlXWy52Sa'
                                      'RFqNJ3CbDMVkpkgrfrQaM=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Izenpe'],
             'submitted_for_inclusion_in_chrome': '2014-11-10',
             'url': 'ct.izenpe.com/'},
            {'contact': 'certificatetransparency@outlook.com; '
                        '+86 (17) 316230-527',
             'description': None,
             'function': 'ceased operation',
             'https_supported': 'yes',
             'id_b64_non_calculated': '4BJ2KekEllZOPQFHmESYqk'
                                      'j4rbFmAOt5AqHvmQmQYnM=',
             'key': None,
             'maximum_merge_delay': 86400,
             'operated_by': ['Beijing PuChuangSiDa '
                             'Technology Ltd.'],
             'submitted_for_inclusion_in_chrome': '2016-11-22',
             'url': 'www.certificatetransparency.cn/ct/'}],
        'special_purpose_logs': [
            {'chrome_inclusion_status': 'Not included',
             'chrome_status': 'not included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'special purpose',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'qJnYeAySkKr0YvMYgMz71S'
                                      'RR6XDQ+/WR73Ww2ZtkVoE=',
             'key': None,
             'maximum_merge_delay': None,
             'notes': 'Log for untrusted roots. Note that this '
                      'log is not trusted by Chrome. It only '
                      'logs certificates that chain to roots '
                      'that are on track for inclusion in '
                      'browser roots or were trusted at some '
                      'previous point. See the announcement blog '
                      'post.',
             'operated_by': ['Google'],
             'started': '2016-03-22',
             'url': 'ct.googleapis.com/submariner/'},
            {'chrome_inclusion_status': 'Not included.',
             'chrome_status': 'not included',
             'contact': 'google-ct-logs@googlegroups.com',
             'description': None,
             'function': 'special purpose',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'HQJLjrFJizRN/YfqPvwJlv'
                                      'dQbyNdHUlwYaR3PEOcJfs=',
             'key': None,
             'maximum_merge_delay': None,
             'notes': 'Log for expired certificates. Note that '
                      'this log is not trusted by Chrome. It '
                      'only logs certificates that have expired. '
                      'See the announcement post.',
             'operated_by': ['Google'],
             'started': '2016-12-19',
             'url': 'ct.googleapis.com/daedalus/'},
            {'description': None,
             'function': 'special purpose',
             'https_supported': 'yes',
             'id_b64_non_calculated': 'sMyD5aX5fWuvfAnMKEkEhy'
                                      'rH6IsTLGNQt8b9JuFsbHc=',
             'key': None,
             'maximum_merge_delay': None,
             'notes': 'Test log. Note that this log is intended '
                      'for testing purposes only and will only '
                      'log certificates that chain to a root '
                      'explicitly added to it. See the '
                      'announcement email.',
             'operated_by': ['Google'],
             'started': '2014-08-25',
             'url': 'ct.googleapis.com/testtube/'}]}
    got = ctlog._logs_dict_from_html(html=input)
    assert got == expected_logs_dict
