---
name: brainstorming
description: Clarify genuinely unresolved goals, constraints or design choices before a new feature or project. Use for requested design discussion; do not reopen decisions or force interviews for clear authorized work.
---

# Brainstorming

> Instruction-only adaptation of the pinned MIT Superpowers workflow; [provenance](../../provenance.json).
> Plugin discovery hooks, visual-companion server/runtime and automatic commits are not imported.

## Understand before choosing

1. Read the brief and the existing source, ownership and relevant guides. Do not ask questions already answered there.
2. Separate supplied requirements from your proposed defaults. State observable outcomes, non-goals, compatibility,
   environment and safety constraints; ask only about a missing decision that materially changes the solution.
3. If the task is clear and already authorized, keep the brief proportional and continue. Do not require another
   approval, a formal design document, a browser or an interview simply because this skill is available.

## Compare meaningful alternatives

Present the smallest alternatives that satisfy the actual requirement, including reuse or no new abstraction.
Explain benefits, costs and risks in the user's vocabulary. Do not expand a folder or scaffold task into app execution.
For a consequential unresolved product choice, let the user decide; settle reversible implementation details with a
clearly identified default instead of repeated permission handoffs.

## Record and check the design

Use the project's maintained spec or issue when it already captures the decision. A durable contract belongs under
`docs/specs`; temporary task planning belongs in ignored `.omx/plans` unless the user chooses another location.
Record purpose, boundaries, chosen approach, rejected options, acceptance and remaining uncertainty—not a transcript.

When an independent readiness check would help and delegation is authorized, use the
[builder-check prompt](builder-check-prompt.md) with a bounded native reviewer. Otherwise self-review the same questions.
Classify findings as already answered, safely decidable or genuinely user-owned; do not silently invent the last category.

For an authorized multi-step implementation, continue with [writing-plans](../writing-plans/SKILL.md) when useful.
For research/design-only work, report the design and stop inside that scope. No automatic commits, branch changes,
runtime launch or mandatory execution-mode selection are implied.
