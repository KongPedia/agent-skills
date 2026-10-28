def cancel(order):
    result = dict(order)
    result["status"] = "cancelled"
    return result
