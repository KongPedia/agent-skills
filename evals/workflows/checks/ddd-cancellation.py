"""External behavioral checks; all requirements are public in CONTRACT.md."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = dict.fromkeys(['open_cancel', 'shipped_guard', 'partial_refund', 'provider_failure', 'retry_once', 'zero_outstanding', 'amount_invariants', 'input_ownership', 'domain_direct'], False)


def check(name, fn):
    try:
        checks[name] = bool(fn())
    except Exception:
        checks[name] = False


def order(status='open'):
    return {'id': 'o1', 'status': status, 'metadata': {'items': ['book']}}


def payment(captured=100, refunded=0, refund_state='none'):
    return {'captured': captured, 'refunded': refunded, 'refund_state': refund_state, 'metadata': {'reference': ['p1']}}


try:
    from checkout import cancel_order
    from ordering import cancel
    from billing import refund

    def open_cancel():
        calls = []
        result, paid = cancel_order(order(), payment(), calls.append)
        return result == order('cancelled') and paid == payment(100, 100, 'refunded') and calls == [100]
    check('open_cancel', open_cancel)

    def shipped_guard():
        calls = []
        try:
            cancel_order(order('shipped'), payment(), calls.append)
        except ValueError:
            return not calls
        return False
    check('shipped_guard', shipped_guard)

    def partial():
        calls = []
        result, paid = cancel_order(order(), payment(100, 40), calls.append)
        return result['status'] == 'cancelled' and paid == payment(100, 100, 'refunded') and calls == [60]
    check('partial_refund', partial)

    def fail(amount):
        raise RuntimeError('provider unavailable')

    def failed():
        result, paid = cancel_order(order(), payment(100, 40), fail)
        return result == order('cancelled') and paid == payment(100, 40, 'failed')
    check('provider_failure', failed)

    def retry():
        first_order, first_payment = cancel_order(order(), payment(100, 40), fail)
        calls = []
        second_order, second_payment = cancel_order(first_order, first_payment, calls.append)
        third_order, third_payment = cancel_order(second_order, second_payment, calls.append)
        return calls == [60] and second_order == third_order == order('cancelled') and second_payment == third_payment == payment(100, 100, 'refunded')
    check('retry_once', retry)

    def no_outstanding():
        calls = []
        return all(refund(payment(n, n), calls.append) == payment(n, n, 'refunded') for n in (0, 100)) and not calls
    check('zero_outstanding', no_outstanding)

    def invariants():
        for captured, refunded in [(-1, 0), (100, -1), (100, 101), (True, 0), (100, False), (1.5, 0), (100, '0')]:
            calls = []
            try:
                refund(payment(captured, refunded), calls.append)
            except ValueError:
                if calls:
                    return False
            else:
                return False
        return True
    check('amount_invariants', invariants)

    def ownership():
        for provider in (lambda _: None, fail):
            original_order, original_payment = order(), payment(100, 40)
            snapshot = copy.deepcopy((original_order, original_payment))
            result, paid = cancel_order(original_order, original_payment, provider)
            if (original_order, original_payment) != snapshot or result is original_order or paid is original_payment:
                return False
        return True
    check('input_ownership', ownership)

    def direct():
        shipped = order('shipped')
        snapshot = copy.deepcopy(shipped)
        try:
            cancel(shipped)
        except ValueError:
            if shipped != snapshot:
                return False
        else:
            return False
        calls = []
        cancelled = cancel(order())
        replay = cancel(cancelled)
        paid = refund(payment(75, 25), calls.append)
        class Unexpected(Exception):
            pass
        def unexpected(_):
            raise Unexpected()
        try:
            refund(payment(), unexpected)
        except Unexpected:
            return replay == order('cancelled') and replay is not cancelled and paid == payment(75, 75, 'refunded') and calls == [50]
        return False
    check('domain_direct', direct)
except Exception:
    pass

passed = all(value is True for value in checks.values())
print('EVAL_RESULT: ' + json.dumps({'status': 'pass' if passed else 'fail', 'checks': checks}))
raise SystemExit(0 if passed else 1)
