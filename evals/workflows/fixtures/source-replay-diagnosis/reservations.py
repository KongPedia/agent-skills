def apply(state, event):
    key = event["request_id"]
    if key in state["seen"]:
        return False
    state["seen"].add(key)
    state["stock"] -= event["quantity"]
    return True
