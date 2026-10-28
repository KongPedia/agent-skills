"""Offline source/evidence case oracle checks. Reference answers stay outside model fixtures."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REFERENCES = {
    'source-retry-units': ('http_retry.py', '''from retry_sdk import delay
def schedule_retry(headers):
    value = headers.get("Retry-After-Ms")
    if value is None:
        return delay()
    milliseconds = int(value)
    if milliseconds < 0:
        raise ValueError("negative delay")
    return delay(milliseconds / 1000)
'''),
    'source-replay-diagnosis': ('incident.json', json.dumps({
        'local_debits': 1, 'duplicate_debit': False,
        'local_skip_reason': 'cursor_after_order', 'production_cause_established': False,
        'evidence_paths': ['reservations.py','dispatch.py','packet.json'],
        'next_evidence': ['Production dispatch cursor and order sequence at the incident time',
                          'Production reservation state and version-matched processing logs'],
    })),
}

def run_check(task, workspace):
    result = subprocess.run([sys.executable,'-B',str(ROOT / task['check'].removeprefix('../')),str(workspace)],capture_output=True,text=True,timeout=15)
    markers = [line.removeprefix('EVAL_RESULT: ') for line in result.stdout.splitlines() if line.startswith('EVAL_RESULT: ')]
    assert len(markers) == 1, result.stderr or result.stdout
    report = json.loads(markers[0])
    assert set(report['checks']) == set(task['expected_checks']), report
    assert result.returncode == (0 if report['status'] == 'pass' else 1), report
    return report

def main():
    catalog = json.loads((ROOT.parents[1] / 'catalog.json').read_text())
    providers = {plugin['id']:plugin for plugin in catalog['plugins']}
    for identity, (filename, reference) in REFERENCES.items():
        task = json.loads((ROOT / 'tasks' / (identity + '.json')).read_text())
        for bundle in task['bundles']:
            assert bundle in providers
            assert set(providers[bundle]['requires']) <= set(task['bundles'])
        for skill in task['required_skills']:
            bundle, name = skill.split(':')
            assert bundle in task['bundles'] and name in providers[bundle]['skills']
        fixture = ROOT / task['fixture'].removeprefix('../')
        with tempfile.TemporaryDirectory(prefix='workflow-source-oracle-') as directory:
            workspace = Path(directory) / 'workspace'
            shutil.copytree(fixture,workspace)
            assert run_check(task,workspace)['status'] == 'fail', identity
            (workspace / filename).write_text('def broken(:' if filename.endswith('.py') else '{broken')
            assert run_check(task,workspace)['status'] == 'fail', identity
            (workspace / filename).write_text(reference)
            assert run_check(task,workspace)['status'] == 'pass', identity
            # Reject the plausible global SDK-unit repair and unsupported production conclusion.
            if identity == 'source-retry-units':
                (workspace / 'retry_sdk.py').write_text('__version__="2.4.0"\ndef delay(seconds=1.0):\n    return {"delay_seconds": seconds/1000}\n')
            else:
                bad = json.loads(reference)
                bad['production_cause_established'] = True
                (workspace / filename).write_text(json.dumps(bad))
            assert run_check(task,workspace)['status'] == 'fail', identity
        print(f'{identity}: broken, syntax and misleading repair/claim rejected; reference accepted; dependency closure valid')

if __name__ == '__main__':
    main()
