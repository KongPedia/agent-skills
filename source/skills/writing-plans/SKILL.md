---
name: writing-plans
description: Turn an accepted specification or clear multi-step requirement into bounded implementation tasks with exact owners, interfaces and verification evidence. Not required for a trivial edit or a new permission gate.
---

# Writing Plans

> Instruction-only adaptation of the pinned MIT Superpowers skill; [provenance](../../skill-sources.json).
> No plugin execution/worktree dependency, automatic commits or mandatory execution-method interview is imported.

## Plan only the missing decisions

Read the requested outcome, existing source and accepted constraints. Do not redesign already agreed behavior or
reverse-specify the entire codebase. A short issue/checklist is sufficient for small work.
Keep temporary plans under ignored `.omx/plans`; maintained product contracts belong in `docs/specs`.
Use another location when explicitly requested. Writing a plan does not authorize implementation of a plan-only task.

## File and dependency map

List the exact files/packages to create or change, their responsibilities, public interfaces and affected consumers.
Preserve native package and lockfile ownership. Group work that changes together; split independent deliverables,
not setup, fixtures and docs away from the behavior they protect. Do not impose file-size caps or empty layers.

## Task contract

When a handoff needs a written brief and no project format exists, use the optional
[task brief](assets/task-brief.md); do not create another record for an already sufficient issue. Each task records:

- Outcome and owned files; other workers and integration owner, if relevant.
- Inputs/outputs and exact interface names needed by neighboring tasks.
- Compatibility, authority, environment and safety constraints.
- Expected failing behavioral assertion and focused regression for a behavior change; characterization for preserved
  behavior; metadata/reference/provenance/diff checks for prose and placeholders.
- Actual authorized verification commands once the package has them, expected evidence, omissions and rollback.

Do not label import errors, missing scaffolding or a not-yet-defined function as a reproduced behavioral bug.
Do not invent a passing build/test command for a directory-only scaffold. Shell commands are proposed steps until run.
Commits, publishing, installation, live services and hardware are separate explicit authorities, not default plan tasks.

## Self-review and handoff

Check every accepted requirement has an owning task, shared types/names agree across tasks, and important error,
cancellation, identity and compatibility cases have evidence. Remove boilerplate that decides nothing.
Keep the plan shorter than an implementation transcript; include code only where an exact algorithm or copy is required.

If execution is already authorized, continue through the available native workflow without another permission round.
If the request is plan-only, deliver the plan and limits. A consequential new ambiguity may need user input;
absence of a preferred orchestration mode does not itself block ordinary implementation.
