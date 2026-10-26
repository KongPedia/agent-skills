# Upstream candidate review

This review selects reusable decision procedures, not the largest possible skill count. The canonical catalog contains
41 procedures after preserving the existing 39 and adding domain modeling and Python type safety. Project-specific
SDK/protocol commands, authority and build environments remain with their consuming repositories.

## Sources and review depth

| Source snapshot | Review performed | Limit |
| --- | --- | --- |
| [Matt Pocock](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2) | Inventory of 38 candidates: 27 shipped, seven in progress, four miscellaneous; candidate scope/overlap assessment | Not a full semantic audit of every supporting resource in all 38 directories |
| [Addy Osmani](https://github.com/addyosmani/agent-skills/tree/aeac41d4d005999432bb7312f7ff06383a91d59d) | All 25 frontmatters and leading procedure bodies checked for scope, triggers and overlap | Not a complete line-by-line audit of all reference files/scripts |
| [wshobson Python type safety](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/python-development/skills/python-type-safety) | Selected procedure/resources inspected for the Python bundle and compatibility/scope adaptation | Does not establish static-type-tool enforcement or runtime input validation |

These immutable references describe the inspected snapshots, not today's upstream state. Imported-file manifests retain
original/local hashes, licenses and narrow adaptations. A candidate inventory is not evidence that every candidate was
fully validated, imported or executed.

## Decisions

| Candidate group | Decision | Reason and application boundary |
| --- | --- | --- |
| Matt's existing `codebase-design` and `writing-for-agents` | Retain | Deep-module/interface and instruction-routing criteria already serve distinct tasks; do not replace their useful resources with summaries |
| Matt's [domain modeling](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/domain-modeling) | Add to common | Concrete domain vocabulary, state/ownership and invariants fill a useful design seam; trigger on actual domain modeling, not mandatory DDD layers for every feature |
| Matt's planning/interview/implementation/review workflows | No blanket import | Existing brainstorming, plans, TDD/SDD, review and debugging already own these decisions; imported workflows must not replace user authority or add approval rituals |
| Matt's issue-tracker/productivity/specialized or in-progress candidates | Defer | Optional external systems and task-specific workflows are not universal language scaffolding; no demonstrated gap requires another default procedure |
| Addy's existing deprecation/migration, observability and security | Retain | They cover distinct compatibility, diagnostic and trust-boundary tasks with project-scoped triggers |
| Addy's broader specification/planning/implementation/review/cleanup procedures | No additional import | Existing procedures cover the need; another author name does not justify duplicate invocation routes |
| Performance guidance | Conditional, not a universal gate | Start from a measured bottleneck and the actual runtime; do not profile or optimize every change by default |
| Python type safety | Add to Python only | Covers public annotations, protocols/generics and actual declared type checks without affecting Next-only projects or treating annotations as runtime validation |
| Additional configuration/style/runtime procedures | Defer unless a concrete gap appears | Existing ownership/configuration/naming/resource boundaries already cover common cases; review unsafe import-time configuration, secret handling or CSV examples before any later adoption |

The two additions keep their full procedure directories and needed resources, with narrow correctness/scope changes
recorded in provenance. New imported revisions have their own source records; an older source pin is not silently
rewritten to make unrelated imports appear upgraded. No new Addy procedure was needed after this comparison.

## Packaging and acceptance boundary

- Exactly one canonical owner per skill; bundles compose the same sources without combination-specific repositories.
- Keep task-triggered monorepo work in common and actual Rust-async guidance in Rust; neither requires an extra option.
- Full referenced resources and required license/NOTICE evidence travel in closed plugin payloads.
- Project commands/contracts/safety are consuming-repository lookups, not copied organization-specific assumptions.
- Frontmatter, hashes, links and package tests prove their own layer, not host installation or LLM compliance.

Public publication is not authorized by this review. Original-material licensing, secrets/proprietary scope and a real
release/host-refresh exercise remain separate decisions and checks. Further additions need a concrete missing use case,
non-overlapping trigger, preserved source evidence and a scoped validation plan—not an additive quota.
