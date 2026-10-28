"""External behavior checks for the public README contract, not architecture style."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = dict.fromkeys(['rename_independent', 'trim', 'invalid_text', 'unknown_key', 'duplicate_casefold', 'own_name', 'order_preserved'], False)


def check(name, fn):
    try:
        checks[name] = bool(fn())
    except Exception:
        checks[name] = False


def raises(kind, fn):
    try:
        fn()
    except kind:
        return True
    return False


try:
    from labels import rename_label
    def independent():
        original = {'a': 'Alpha', 'b': 'Beta'}
        updated = rename_label(original, 'a', 'Gamma')
        return updated == {'a': 'Gamma', 'b': 'Beta'} and original == {'a': 'Alpha', 'b': 'Beta'} and updated is not original
    check('rename_independent', independent)
    check('trim', lambda: rename_label({'a': 'Alpha'}, 'a', '  New  ') == {'a': 'New'})
    check('invalid_text', lambda: all(raises(ValueError, lambda value=value: rename_label({'a': 'Alpha'}, 'a', value)) for value in ('', '  ', 'x' * 31, 1, None, True)) and rename_label({'a': 'Alpha'}, 'a', 'x' * 30) == {'a': 'x' * 30})
    check('unknown_key', lambda: raises(KeyError, lambda: rename_label({'a': 'Alpha'}, 'missing', 'New')))
    def duplicates():
        for text in (' BETA ', 'beta', 'STRASSE'):
            original = {'a': 'Alpha', 'b': 'Beta', 'c': 'Straße'}
            if not raises(ValueError, lambda: rename_label(original, 'a', text)) or original != {'a': 'Alpha', 'b': 'Beta', 'c': 'Straße'}:
                return False
        return True
    check('duplicate_casefold', duplicates)
    check('own_name', lambda: rename_label({'a': 'Alpha', 'b': 'Beta'}, 'a', ' ALPHA ') == {'a': 'ALPHA', 'b': 'Beta'})
    check('order_preserved', lambda: list(rename_label({'c': 'Third', 'a': 'First', 'b': 'Second'}, 'a', 'Renamed')) == ['c', 'a', 'b'])
except Exception:
    pass

passed = all(value is True for value in checks.values())
print('EVAL_RESULT: ' + json.dumps({'status': 'pass' if passed else 'fail', 'checks': checks}))
raise SystemExit(0 if passed else 1)
