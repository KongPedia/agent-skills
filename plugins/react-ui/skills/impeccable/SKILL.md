---
name: impeccable
description: "Use when auditing or critiquing web UI design, polishing an existing interface, or hardening its loading, error, accessibility and content states. Covers hierarchy, typography, color, responsive behavior and product-specific design rather than generic AI templates. Not for backend-only work or an implied redesign."
license: Apache-2.0
metadata:
  version: 4.7.1
---

# Impeccable

> Modified for Project Blueprints: selected instruction-only workflows from Impeccable 4.7.1.
> This is not the upstream runtime/plugin: no launcher, detector, hooks, browser overlay, storage commands,
> bundled subagents or binaries are installed. Applicable `AGENTS.md` and `.agents/README.md` retain authority.

Bring a clear point of view, product understanding and careful craft to frontend work. Avoid interchangeable
SaaS templates by making hierarchy, content and interaction belong to the actual product, not by adding novelty.
On working product surfaces, precision and restraint often show more craft than decoration.

## Scope and context

1. Read applicable project guidance and `DESIGN.md` before visual work. Inspect the current target, tokens,
   shared components and neighboring flows. Use existing product/brief evidence; do not invent missing audience,
   claims or features, and do not create or overwrite product/design documents as setup.
2. Resolve a concrete component, route or surface and select the matching workflow below. A missing design
   document does not make an established product greenfield. Preserve the brief, content, behavior and visual
   identity unless redesign is actually requested.
3. For editing, read [reference/craft-floor.md](reference/craft-floor.md) after direction is settled.
   Its aesthetic examples are heuristics, never authority to replace established operator layout or tokens.
4. Inspect rendered states only when the requested scope permits browser/application execution. With source
   or supplied screenshots alone, name the missing evidence rather than claiming visual, interaction or a11y
   validation. This skill grants no hardware, publishing, dependency or service-start authority.

## Modes

Choose by what success means on the specific surface:

- **Operate:** the visitor completes a task: app UI, dashboards, admin, settings and tools. Scanability,
  consistency, native expectations and the usage scene outrank expression. Read [reference/operate.md](reference/operate.md).
- **Read:** the visitor understands docs, articles or guides. Structure for comprehension; use the typography
  and consistency considerations in [reference/operate.md](reference/operate.md), not dashboard density.
- **Persuade:** the visitor decides and acts: marketing, campaigns or pricing. A distinctive point of view
  can earn attention, but preserve factual claims and the requested brief.
- **Experience:** the visitor engages with the work itself: portfolios, galleries and showcases.
  Let the artifact lead rather than imposing a generic product shell.

## Supported workflows

These are requests to the agent, not installed executable commands. Load only the reference needed now.

| Request | Reference | Outcome |
| --- | --- | --- |
| `$impeccable audit <target>` | [reference/audit.md](reference/audit.md) | Read-only technical UI findings with evidence and limits |
| `$impeccable critique <target>` | [reference/critique.md](reference/critique.md) | Read-only hierarchy, usability, specificity and persona assessment |
| `$impeccable polish <target>` | [reference/polish.md](reference/polish.md) | Scoped refinement within the incumbent visual world |
| `$impeccable harden <target>` | [reference/harden.md](reference/harden.md) | Scoped resilience for content, input, errors and interrupted state |

A plain `$impeccable` request uses the user's existing target and intent; ask only for a material missing target
or decision. Do not auto-run setup or a repository-wide audit. For other design work, use the existing
`frontend-design` entrypoint and project design workflow rather than inventing unsupported Impeccable commands.

## Working constraints

- **The brief wins.** Respect pinned aesthetics, fonts, palette, density and eras. Anti-template heuristics
  identify unreasoned defaults, not forbidden styles. Preserve legitimate tactical data labels, status colors,
  dense panels and shared components when the operator use case needs them.
- **Refinement preserves; redesign replaces only when requested.** Do not smuggle a replacement world into polish,
  change factual copy, or duplicate a design-system source of truth. Accessibility and safety remain required.
- Keep expressive work grounded in the subject without importing hateful or supremacist decorative symbols.
- Use existing tools and role routing only where useful and available. Independent review, when used, is
  reported as actual evidence; a solo/manual assessment is not a detector or dual-agent run.
- Audit and critique report findings without edits. Authorized polish/harden work follows project regression
  and application verification gates; prose-only work stays static. Examples do not authorize new dependencies,
  backend contracts, i18n systems or features outside scope.

## Evidence and delivery

Report the target and method first: source-only, supplied capture, or actually rendered/interactive states.
For findings give location, user impact, confidence and the smallest useful repair. Distinguish measured defects
from design judgments and unverified possibilities. Do not certify WCAG conformance from a heuristic score.
End with changed boundaries (if any), actual checks, omitted checks and remaining risk. No automatic report
archive, trend storage or product-document mutation is part of this portable import.
