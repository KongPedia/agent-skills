"""Validate DDD oracles offline; reference repairs are not agent-visible fixtures."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REFERENCES = {
    'ddd-cancellation': {
        'ordering.py': '''def cancel(order):
    if order['status'] == 'shipped':
        raise ValueError('already shipped')
    return dict(order, status='cancelled')
''',
        'billing.py': '''def refund(payment, send_refund):
    captured, refunded = payment['captured'], payment['refunded']
    if type(captured) is not int or type(refunded) is not int or not 0 <= refunded <= captured:
        raise ValueError('invalid amounts')
    remaining = captured - refunded
    result = dict(payment)
    if remaining:
        try:
            send_refund(remaining)
        except RuntimeError:
            result['refund_state'] = 'failed'
            return result
    result.update(refunded=captured, refund_state='refunded')
    return result
''',
    },
    'ddd-labels': {
        'labels.py': '''def rename_label(labels, key, text):
    if key not in labels:
        raise KeyError(key)
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 30:
        raise ValueError('invalid label')
    text = text.strip()
    if any(other != key and label.casefold() == text.casefold() for other, label in labels.items()):
        raise ValueError('duplicate label')
    result = dict(labels)
    result[key] = text
    return result
''',
    },
}


def run_check(manifest, workspace):
    checker = (ROOT / 'tasks' / manifest['check']).resolve()
    result = subprocess.run([sys.executable, '-B', str(checker), str(workspace)], text=True, capture_output=True, timeout=20)
    markers = [line.removeprefix('EVAL_RESULT: ') for line in result.stdout.splitlines() if line.startswith('EVAL_RESULT: ')]
    assert len(markers) == 1, result.stderr or result.stdout
    report = json.loads(markers[0])
    assert set(report['checks']) == set(manifest['expected_checks']), report
    assert result.returncode == (0 if report['status'] == 'pass' else 1), report
    return report



def proposal_reference():
    return {
        'status': 'proposed',
        'facts': {'login_context': 'identity', 'membership_context': 'workspaces', 'global_suspension_scope': 'all_workspaces', 'membership_removal_scope': 'one_workspace', 'workspace_temporary_suspension_exists': False, 'running_session_revocation_proven': False},
        'existing_terms': [
            {'context': 'identity', 'term': 'Account', 'meaning': 'Global login principal'},
            {'context': 'identity', 'term': 'Member', 'meaning': 'Informal support name for the login person'},
            {'context': 'workspaces', 'term': 'Account', 'meaning': 'Customer organization tenant workspace'},
            {'context': 'workspaces', 'term': 'Member', 'meaning': 'Membership linking one person to one workspace'},
        ],
        'evidence': [
            {'path': 'identity/GLOSSARY.md', 'supports': 'Identity meanings of Account and Member'},
            {'path': 'workspaces/GLOSSARY.md', 'supports': 'Workspace-specific Account/Member meanings'},
            {'path': 'identity/accounts.py', 'supports': 'Global sign-in status'},
            {'path': 'workspaces/access.py', 'supports': 'Membership removal and access gating without session revocation'},
            {'path': 'docs/adr/0001-separate-identity-and-memberships.md', 'supports': 'Accepted separation, not a temporary suspension implementation'},
        ],
        'proposal': {'capability': 'Workspace access hold', 'owner': 'Workspaces access policy', 'recommendation': 'Use a separate workspace hold while preserving membership identity; more policy combinations but avoids conflating removal and reversible access restriction.'},
        'alternatives': [
            {'model': 'Membership lifecycle suspended state', 'benefit': 'One lifecycle surface', 'cost': 'Reinstatement must restore prior membership state and temporary restriction becomes a membership lifecycle concern'},
            {'model': 'Orthogonal workspace access hold', 'benefit': 'Keeps membership lifecycle independent', 'cost': 'Access combines two state dimensions and must define removal/hold interactions'},
        ],
        'open_questions': ['Who may place or release a workspace access hold?', 'Should already-issued sessions be revoked, and how is reinstatement authorized?'],
        'implementation_changed': False, 'accepted_decisions_changed': False,
    }


def check_proposal(manifest, workspace):
    destination = workspace / 'proposal.json'
    assert run_check(manifest, workspace)['status'] == 'fail'
    reference = proposal_reference()
    for alternative in (False, True):
        value = copy.deepcopy(reference)
        if alternative:
            value['proposal'] = {'capability': 'Paused membership', 'owner': 'Membership lifecycle in Workspaces', 'recommendation': 'Prefer an explicit suspended membership state for one authoritative lifecycle; validate allowed reinstatement transitions and cross-workspace isolation before acceptance.'}
        destination.write_text(json.dumps(value))
        assert run_check(manifest, workspace)['status'] == 'pass', value
    for field, wrong in [('global_suspension_scope', 'one_workspace'), ('membership_removal_scope', 'all_workspaces'), ('workspace_temporary_suspension_exists', True), ('running_session_revocation_proven', True), ('login_context', 'workspaces'), ('membership_context', 'identity')]:
        value = copy.deepcopy(reference)
        value['facts'][field] = wrong
        destination.write_text(json.dumps(value))
        rejected = run_check(manifest, workspace)
        assert rejected['status'] == 'fail' and not rejected['checks']['context_facts'], rejected
    for field, wrong in [('status', 'accepted'), ('implementation_changed', True), ('accepted_decisions_changed', True)]:
        value = copy.deepcopy(reference)
        value[field] = wrong
        destination.write_text(json.dumps(value))
        rejected = run_check(manifest, workspace)
        assert rejected['status'] == 'fail' and not rejected['checks']['proposal_not_implementation'], rejected
    destination.write_text('invalid JSON !!!')
    invalid = run_check(manifest, workspace)
    assert invalid['status'] == 'fail' and not any(invalid['checks'].values()), invalid
    print('ddd-domain-evolution: two valid model proposals accepted; missing/invalid/factual/status mutants rejected; 7 checks')


def main():
    for path in sorted((ROOT / 'tasks').glob('ddd-*.json')):
        manifest = json.loads(path.read_text())
        fixture = (path.parent / manifest['fixture']).resolve()
        with tempfile.TemporaryDirectory(prefix='ddd-oracle-') as temporary:
            workspace = Path(temporary) / 'workspace'
            shutil.copytree(fixture, workspace)
            if manifest['id'] == 'ddd-domain-evolution':
                check_proposal(manifest, workspace)
                continue
            broken = run_check(manifest, workspace)
            assert broken['status'] == 'fail', (manifest['id'], broken)
            for name, source in REFERENCES[manifest['id']].items():
                (workspace / name).write_text(source)
            repaired = run_check(manifest, workspace)
            assert repaired['status'] == 'pass', (manifest['id'], repaired)
            if manifest['id'] == 'ddd-cancellation':
                ordering_source = (workspace / 'ordering.py').read_text()
                checkout_source = (workspace / 'checkout.py').read_text()
                (workspace / 'ordering.py').write_text(ordering_source.replace("    if order['status'] == 'shipped':\n        raise ValueError('already shipped')\n", ''))
                (workspace / 'checkout.py').write_text(checkout_source.replace('    return cancel(order), refund(payment, send_refund)', "    if order['status'] == 'shipped':\n        raise ValueError('already shipped')\n    return cancel(order), refund(payment, send_refund)"))
                misplaced = run_check(manifest, workspace)
                assert misplaced['status'] == 'fail' and not misplaced['checks']['domain_direct'], misplaced
                assert misplaced['checks']['shipped_guard'], misplaced
                (workspace / 'ordering.py').write_text(ordering_source)
                (workspace / 'checkout.py').write_text(checkout_source)
            # Public API guards must detect a policy regression, not just fixture syntax errors.
            target = 'billing.py' if manifest['id'] == 'ddd-cancellation' else 'labels.py'
            source = (workspace / target).read_text()
            mutant = source.replace('remaining = captured - refunded', 'remaining = captured') if target == 'billing.py' else source.replace('label.casefold() == text.casefold()', 'label == text')
            (workspace / target).write_text(mutant)
            assert run_check(manifest, workspace)['status'] == 'fail', manifest['id']
            (workspace / target).write_text('invalid Python syntax !!!')
            invalid = run_check(manifest, workspace)
            assert invalid['status'] == 'fail' and not any(invalid['checks'].values()), invalid
            print(f"{manifest['id']}: broken/syntax/mutant rejected; reference passed {len(repaired['checks'])} checks")
    print('Three DDD external oracles validated; no model or auth calls.')


if __name__ == '__main__':
    main()
