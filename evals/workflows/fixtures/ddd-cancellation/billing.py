def refund(payment, send_refund):
    result = dict(payment)
    send_refund(payment["captured"])
    result["refunded"] = payment["captured"]
    result["refund_state"] = "refunded"
    return result
