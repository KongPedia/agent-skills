"""Factual/format oracle only; model quality requires independent semantic review."""
import json
from pathlib import Path
import sys

workspace = Path(sys.argv[1]).resolve()
checks = dict.fromkeys(['proposal_schema', 'context_facts', 'existing_term_coverage', 'evidence_paths', 'competing_models', 'unresolved_questions', 'proposal_not_implementation'], False)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def record(value, fields):
    return isinstance(value, dict) and all(text(value.get(key)) for key in fields)


try:
    proposal = json.loads((workspace / 'proposal.json').read_text())
    required = {'status', 'facts', 'existing_terms', 'evidence', 'proposal', 'alternatives', 'open_questions', 'implementation_changed', 'accepted_decisions_changed'}
    checks['proposal_schema'] = isinstance(proposal, dict) and required <= proposal.keys() and record(proposal.get('proposal'), ('capability', 'owner', 'recommendation'))
    facts = proposal.get('facts', {})
    expected = {'login_context': 'identity', 'membership_context': 'workspaces', 'global_suspension_scope': 'all_workspaces', 'membership_removal_scope': 'one_workspace', 'workspace_temporary_suspension_exists': False, 'running_session_revocation_proven': False}
    checks['context_facts'] = isinstance(facts, dict) and all(type(facts.get(key)) is type(value) and facts.get(key) == value for key, value in expected.items())
    terms = proposal.get('existing_terms', [])
    checks['existing_term_coverage'] = isinstance(terms, list) and len(terms) == 4 and all(record(item, ('context', 'term', 'meaning')) for item in terms) and {(item['context'], item['term']) for item in terms} == {(context, term) for context in ('identity', 'workspaces') for term in ('Account', 'Member')}
    evidence = proposal.get('evidence', [])
    def valid_evidence(item):
        if not record(item, ('path', 'supports')):
            return False
        path = Path(item['path'])
        target = (workspace / path).resolve()
        return not path.is_absolute() and '..' not in path.parts and target.is_relative_to(workspace) and target.is_file() and item['path'] != 'proposal.json'
    checks['evidence_paths'] = isinstance(evidence, list) and bool(evidence) and all(valid_evidence(item) for item in evidence)
    alternatives = proposal.get('alternatives', [])
    checks['competing_models'] = isinstance(alternatives, list) and len(alternatives) >= 2 and all(record(item, ('model', 'benefit', 'cost')) for item in alternatives) and len({item['model'].casefold().strip() for item in alternatives}) == len(alternatives)
    questions = proposal.get('open_questions', [])
    checks['unresolved_questions'] = isinstance(questions, list) and len(questions) >= 2 and all(text(item) for item in questions)
    checks['proposal_not_implementation'] = proposal.get('status') == 'proposed' and proposal.get('implementation_changed') is False and proposal.get('accepted_decisions_changed') is False
except Exception:
    pass

passed = all(value is True for value in checks.values())
print('EVAL_RESULT: ' + json.dumps({'status': 'pass' if passed else 'fail', 'checks': checks}))
raise SystemExit(0 if passed else 1)
