"""A small caller-clock idempotency store; claim returns new versus replay."""
class Ledger:
    def __init__(self, ttl, capacity):
        self.ttl = ttl
        self.capacity = capacity
        self.entries = {}

    def claim(self, key, payload, now):
        if key in self.entries:
            return False
        self.entries[key] = payload
        return True
