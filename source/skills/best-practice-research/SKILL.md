---
name: best-practice-research
description: Research current best practices, technical reference implementations or version-sensitive guidance using primary sources and the owning repository's actual constraints. Not a dependency installer or automatic implementation workflow.
---

# Best-Practice Research

> Adapted from the pinned MIT oh-my-codex skill. [Provenance](../../skill-sources.json)
> and [license](../../licenses/oh-my-codex-LICENSE) identify the original source. OMX runtime commands are not required.

## Scope

Gather the smallest evidence set that can change the decision. A research-only request stays read-only; an already
authorized implementation task may use these findings and continue without another workflow-switch approval.
This skill does not grant installation, commit, publishing, service, CI, deployment or hardware authority.

## Procedure

1. Identify the question, affected package, intended runtime, versions and evidence needed. Inspect relevant source,
   callers, manifests, locks and existing guides before recommending a replacement pattern.
2. Separate repository facts from external behavior. For external APIs and version-sensitive facts, prefer official
   documentation, upstream source, release notes and original authors. Record exact URLs and the inspected revision/date.
3. Compare alternatives only when a real adoption decision exists. Account for maintenance, compatibility, cost,
   additional runtime dependencies and local adaptations. Existing compatible utilities are the first alternative.
4. Extract the reusable part of an example. Distinguish packaging, architecture, test policy and illustrative application
   behavior; do not copy a whole starter or host plugin to obtain a few instructions.
5. Return a recommendation, supporting sources, uncertainty, affected consumers and the smallest next action within
   the user's scope. Mark inferred conclusions explicitly; configuration is not execution evidence.

## Completion

- The recommendation is linked to direct primary evidence and current local constraints.
- Facts, proposals and untested behavior are distinguishable.
- Research-only work has made no unrequested changes. An implementation handoff retains existing authorization,
  file ownership, compatibility limits and scope-appropriate verification.

Use native research or dependency-review roles only when available and useful; role names are responsibilities,
not a requirement to install an orchestration framework.
