"""Vendored retry SDK 2.4.0. Public delay API accepts seconds."""
__version__ = "2.4.0"
def delay(seconds=1.0):
    if seconds < 0:
        raise ValueError("negative delay")
    return {"delay_seconds": float(seconds)}
