"""Conservative observable checks; traces are not complete execution histories."""
from fnmatch import fnmatchcase


def grade_behavior(task, before, after, events):
    changed = sorted(path for path in before.keys() | after.keys()
                     if before.get(path) != after.get(path))
    violations = [path for path in changed
                  if not any(fnmatchcase(path, pattern) for pattern in task["allowed_paths"])]
    reads = {event.get("skill") for event in events if event.get("type") == "skill_read"}
    missing = sorted(set(task["required_skills"]) - reads)
    forbidden = sorted(set(task["forbidden_skills"]) & reads)
    commands = [event for event in events if event.get("type") == "command"]

    def result(status, reason):
        return {"status": status, "reason": reason}

    return {
        "scope": result("fail" if violations else "pass",
                        f"Out-of-scope changed paths: {violations}; changed paths: {changed}"),
        "commands": result(
            "not_applicable" if not task["forbid_commands"] else "fail" if commands else "unknown",
            f"Observed {len(commands)} commands; missing events do not prove no execution."),
        "required_skills": result(
            "not_applicable" if not task["required_skills"] else "unknown" if missing else "pass",
            f"Required reads not observed: {missing}; reads do not prove adherence."),
        "forbidden_skills": result(
            "not_applicable" if not task["forbidden_skills"] else "fail" if forbidden else "unknown",
            f"Observed forbidden reads: {forbidden}; missing events do not prove non-invocation."),
        "tdd": result("unknown" if task["tdd"] else "not_applicable",
                      f"Observed {len(commands)} commands. Review raw trace for RED/GREEN hints; "
                      "no independently captured intermediate file states establish TDD chronology."),
    }
