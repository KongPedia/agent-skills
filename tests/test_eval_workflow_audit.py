"""Post-hoc oracle diagnostics use synthetic repairs, never actual model artifacts."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'evals/workflows/checks/ddd-labels.py'
AUDIT = ROOT / 'evals/audits/ddd-labels-string-domain-2026-10-28.py'
CHECKS = {'rename_independent', 'trim', 'invalid_text', 'unknown_key', 'duplicate_casefold', 'own_name', 'order_preserved'}
REFERENCE = '''def rename_label(labels, key, text):
    if key not in labels:
        raise KeyError(key)
    if not isinstance(text, str):
        raise {exception}('text must be str')
    text = text.strip()
    if not 1 <= len(text) <= 30:
        raise ValueError('invalid length')
    if any(other != key and label.casefold() == text.casefold() for other, label in labels.items()):
        raise ValueError('duplicate label')
    result = labels.copy()
    result[key] = text
    return result
'''


def run_checker(checker, workspace):
    result = subprocess.run([sys.executable, '-B', str(checker), str(workspace)], text=True, capture_output=True, timeout=10)
    markers = [line.removeprefix('EVAL_RESULT: ') for line in result.stdout.splitlines() if line.startswith('EVAL_RESULT: ')]
    assert len(markers) == 1, result.stderr or result.stdout
    report = json.loads(markers[0])
    assert set(report['checks']) == CHECKS
    assert result.returncode == (0 if report['status'] == 'pass' else 1), report
    return report


def test_frozen_oracle_rejects_publicly_valid_typeerror_variant(tmp_path):
    (tmp_path / 'labels.py').write_text(REFERENCE.format(exception='TypeError'))
    report = run_checker(FROZEN, tmp_path)
    assert report['status'] == 'fail'
    assert report['checks']['invalid_text'] is False
    assert all(value for key, value in report['checks'].items() if key != 'invalid_text')


@pytest.mark.parametrize('exception', ['TypeError', 'ValueError'])
def test_string_domain_diagnostic_accepts_both_nonstring_exception_policies(tmp_path, exception):
    (tmp_path / 'labels.py').write_text(REFERENCE.format(exception=exception))
    report = run_checker(AUDIT, tmp_path)
    assert report['status'] == 'pass', report
    assert all(report['checks'].values())


@pytest.mark.parametrize(('old', 'new', 'failed_check'), [
    ('if not 1 <= len(text) <= 30:', 'if len(text) > 30:', 'invalid_text'),
    ('if not 1 <= len(text) <= 30:', 'if len(text) == 0:', 'invalid_text'),
    ('label.casefold() == text.casefold()', 'label == text', 'duplicate_casefold'),
])
def test_string_domain_diagnostic_still_rejects_public_contract_violations(tmp_path, old, new, failed_check):
    source = REFERENCE.format(exception='TypeError').replace(old, new)
    (tmp_path / 'labels.py').write_text(source)
    report = run_checker(AUDIT, tmp_path)
    assert report['status'] == 'fail'
    assert report['checks'][failed_check] is False
