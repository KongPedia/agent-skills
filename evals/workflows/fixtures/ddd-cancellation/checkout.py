from ordering import cancel
from billing import refund


def cancel_order(order, payment, send_refund):
    return cancel(order), refund(payment, send_refund)
