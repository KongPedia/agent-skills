"""Checkout reservation: reserve returns independent stock; caller owns all inputs."""
def reserve(stock, lines):
    for sku, quantity in lines:
        stock[sku] -= quantity
    return stock
