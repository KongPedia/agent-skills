---
name: spec-driven-development
description: Maintain a specification for meaningful behavior, compatibility, or cross-package changes, with explicit proposed/current status and verification evidence. Not mandatory ceremony for small fixes or prose edits.
---

# Specification-driven development

SDD here means **specification-driven development**, not subagent-driven development. Use a specification when it
reduces ambiguity or coordinates a contract; a clear issue or task brief is sufficient for a small change.

## Workflow

1. **Find the current contract.** Inspect implementation, consumers, tests and maintained specs. Record the outcome,
   owner, compatibility constraints, exclusions and observable acceptance criteria. Keep an existing sufficient
   record rather than creating a duplicate specification.
2. **Separate authority from intent.** Maintain durable product/technical contracts under `docs/specs/` with an
   explicit proposed, implementing, current or superseded status. A proposal describes intended behavior, not
   verified support. Temporary decomposition and review scratch may use ignored `.omx/plans/`; that directory is
   optional scratch, not an application dependency or required workflow runtime.
3. **Resolve only missing decisions.** Use the [change specification template](assets/change-spec.md) when
   needed. Continue already authorized, clear local work without another approval checkpoint. Ask only about
   material ambiguity, destructive actions or additional authority; a spec does not grant release or live access.
4. **Implement against the acceptance boundary.** Use failing behavioral regression evidence for changed behavior,
   characterization for preserved behavior, and static checks for prose. Update every active consumer for shared
   contracts; select the cross-package procedure when available in the [local catalog](../../README.md),
   and account for producer/consumer ownership even when the affected consumer is external to this repository.
5. **Reconcile the record.** After verification, update affected current specs and documentation with actual
   behavior, evidence and remaining limits. Keep unresolved intent proposed; link a superseded record to its
   replacement. Use [ADR records](../../../docs/adr/README.md) for consequential decisions and rationale, not a
   second copy of the behavioral contract.

## Output and limits

Deliver a maintained contract or a link to the sufficient existing record, acceptance-to-evidence mapping,
consumer coverage, compatibility/rollback notes and explicitly unverified items.
Spec Kit and OpenSpec are [reference approaches](../../references/development.md#reference-approaches), not installed
tools or required file formats. Their adoption, generation and dependencies require a separately scoped decision.
