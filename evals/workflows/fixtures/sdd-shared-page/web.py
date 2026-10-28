from provider import list_tasks


def render_tasks(records):
    return [task["title"] for task in list_tasks(records)]
