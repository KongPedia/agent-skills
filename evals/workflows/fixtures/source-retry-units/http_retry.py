from retry_sdk import delay
def schedule_retry(headers):
    value = headers.get("Retry-After-Ms")
    if value is None:
        return delay()
    milliseconds = int(value)
    if milliseconds < 0:
        raise ValueError("negative delay")
    return delay(milliseconds)
