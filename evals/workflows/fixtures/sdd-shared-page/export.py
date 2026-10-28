from provider import list_tasks


def export_ids(records):
    return [task["id"] for task in list_tasks(records)]
