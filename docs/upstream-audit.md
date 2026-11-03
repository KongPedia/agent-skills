# Upstream candidate review

This review selects reusable decision procedures, not the largest possible skill count. The canonical catalog contains
42 procedures after preserving the existing 39 and adding domain modeling, Python type safety and UI UX Pro Max. Project-specific
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

## Frontend and UI/UX candidates

On 2026-11-02, a targeted review compared widely used UI/UX resources with the five existing `react-ui` skills.
GitHub stars were used only to find candidates, not as evidence of skill quality, installation or model adherence.
The [frontend workflow guide](frontend-workflows.md) maps the retained procedures to design, critique, accessibility,
React performance and composition; the existing evaluations do not yet cover UI tasks.

| Inspected candidate | Decision on 2026-11-02 | Reason and limit |
| --- | --- | --- |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/3a13158ff1f32156cbe144108de48eda2ecaed9a) | Defer | Design search/data overlaps existing guidance. Its Python search tooling and Claude plugin-root paths need host-specific compatibility and behavioral evaluation before an unmodified portable import. |
| [Microsoft Playwright CLI skill](https://github.com/microsoft/playwright-cli/tree/c2d8d199459d1480491bebf0a6b3587136b673fa) | Defer | Useful optional browser tooling, but it needs a CLI/browser runtime. A shared skill does not authorize installation, destructive browser actions or application execution. |
| Existing Anthropic frontend-design, Impeccable and Vercel UI skills | Retain | They already cover design direction, UI critique/polish, interface review, React performance and composition; Impeccable here is an instruction-only adaptation, not its upstream runtime. |

The 2026-11-02 comparison imported no new skill or runtime. The separately authorized addition below supersedes
UI UX Pro Max's deferral; the other decisions remain unchanged.

### UI UX Pro Max addition, 2026-11-03

The user subsequently requested UI UX Pro Max and its selection during UI work. The `react-ui` bundle now owns
`ui-ux-pro-max`, pinned to [upstream `713eef51b04efc98d6fa565323b495f7c9c89fd4`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/713eef51b04efc98d6fa565323b495f7c9c89fd4).
The import retains the procedure and its needed standard-library Python search/data, with immutable upstream hashes,
reviewed local adaptations and MIT license evidence in the [central ledger](../provenance/skill-sources.json). It excludes the upstream installer,
marketplace/plugin setup, hooks and host/browser/MCP configuration.
Reviewed runtime adaptations stop design generation on data-read failures and reject symlinked managed persistence
paths before writing. These narrow safety changes have separate local hashes; upstream hashes remain immutable.

Selection covers visual creation, redesign and polish, including style, palette, typography, layout and dashboard UX
choices. It complements existing design/refinement entrypoints instead of replacing them; nonvisual frontend and
backend-only fixes stay outside that trigger. Existing product design, real content/telemetry, interactions and native
framework constraints win over catalog suggestions. Search is read-only by default; optional persistence needs explicit
write scope. The [frontend workflow guide](frontend-workflows.md) owns the task map.

This is an authorized source/packaging and routing addition, not evidence of fresh-session discovery, model adherence,
rendered UI improvement or accessibility conformance. Existing behavior evaluations do not cover UI tasks, and their
frozen inputs and outcomes are unchanged. Host refresh and actual UI-result comparison remain separate evidence layers.

## Packaging and acceptance boundary

- Exactly one canonical plugin owner per skill; bundles install directly from those Git-managed skill directories,
  without a second source tree or combination-specific repositories.
- Keep task-triggered monorepo work in common and actual Rust-async guidance in Rust; neither requires an extra option.
- Full referenced resources and required license/NOTICE evidence travel in closed plugin payloads.
- Project commands/contracts/safety are consuming-repository lookups, not copied organization-specific assumptions.
- Frontmatter, hashes, links and package tests prove their own layer, not host installation or LLM compliance.

Public publication is not authorized by this review. Original-material licensing, secrets/proprietary scope and a real
release/host-refresh exercise remain separate decisions and checks. Further additions need a concrete missing use case,
non-overlapping trigger, preserved source evidence and a scoped validation plan—not an additive quota.
