def pending(orders, cursor):
    return [order for order in orders if order["sequence"] > cursor]
