# KongLabs Agent Skills

One versioned organization source for reusable engineering skills and **optional** advisory hooks. Language and
framework bundles are folders in this repository, not separate repositories and not one repository per combination.

**First-release repositories:** [KongPedia/agent-skills](https://github.com/KongPedia/agent-skills) and
[KongPedia/project-blueprints](https://github.com/KongPedia/project-blueprints), with matching `v0.1.0` tags/releases.
Existing releases do not authorize new publication or visibility changes. A marketplace is a plugin index, not a public
store: this checkout or a reviewed Git source works without a directory listing.

## First-run recovery: plugin not found

If Codex reports `plugin X not found in marketplace konglabs-agent-skills`, first check whether the reviewed source
has been registered on this host. If not, register it **once**:

```bash
codex plugin marketplace add /path/to/agent-skills
```

Or, from this `agent-skills` checkout:

```bash
codex plugin marketplace add .
```

Then retry the selected adds, or inspect the destination before retrying Copier. If that marketplace name is already
registered, inspect its source/revision instead of automatically retargeting it: Codex can reuse a stale same-name Git
cache. Changed URL/ref settings alone do not attest installed bytes. See [host setup](docs/hosts.md).

## Generate through native Copier

With Codex available and the reviewed marketplace registered, use the private template through native Git authentication:

```bash
uvx copier copy --trust https://github.com/KongPedia/project-blueprints.git ./my-project
```

Review the template/revision before `--trust`: this authorizes template tasks, including selected native Codex adds,
not Codex workspace/hook trust. Use `--skip-tasks` instead of `--trust` for rendering only or Claude/manual provisioning.
There is no custom creation CLI or strict existing-destination guard; choose a new target and inspect partial output
before retrying. Generated `.agents/plugin-setup.md` keeps selected recovery/Claude commands. Source registration,
installation, activation, trust and actual session loading remain separate.

## Two repositories, different jobs

| Repository | Owns |
| --- | --- |
| `agent-skills` | Reusable skill bodies/resources, source licenses, plugin bundles, opt-in advisory hook |
| `project-blueprints` | Native Copier questions/layouts, project-owned contracts and plugin activation/provisioning |
| Generated product | Actual commands, native manifests, domain contracts, project-local rules and safety decisions |
| Agent host | Download/cache, explicit activation, trust, authentication, refresh and session discovery |

Shared skill bodies stay with the provider and host cache, not as Markdown copies in generated products. Different
developers still need their own source registration, installation and refresh. Existing products need no new skill-file
commit just to receive a refreshed, already-enabled bundle on that host.

## Structure

For the current folder map, editable/generated ownership, hook and role TOML locations, see the
[repository structure guide (한국어)](docs/repository-structure.md). The hook remains in `session-guidance`;
the four canonical role TOMLs remain in Common's `exports/codex/agents/`.

```text
catalog.json                                  # Stable bundle owners, version and composition metadata
plugins/<bundle>/skills/<skill>/               # Canonical procedures/resources; edit these
plugins/<owner>/references/                    # Canonical shared references owned by that plugin
plugins/<owner>/licenses/                      # Canonical license/NOTICE evidence owned by that plugin
plugins/common/exports/codex/agents/*.toml      # Canonical generic roles; explicit Codex provisioning artifacts
plugins/session-guidance/hooks/session-start.sh # Canonical optional printf-only advisory
provenance/skill-sources.json                  # Reviewed canonical paths/hashes and immutable upstream evidence
scripts/build_plugins.py                      # Standard-library validation/preparation and --check
.agents/plugins/marketplace.json              # Generated Codex marketplace adapter
.claude-plugin/marketplace.json                # Generated Claude marketplace adapter
```

Each `plugins/<bundle>/` is both the authoring home and an installable package with root `plugin.json`;
skill-bearing bundles also have `skills/`. A bundle and plugin are the same installation unit here; there is no second skill tree under `source/`.
Project-local `.agents/skills/` is a separate discovery mechanism, not a required copy of the shared skills.
Each plugin's root `plugin.json` is the portable format; `.codex-plugin/plugin.json` is an optional Codex
compatibility location rather than a second authored package.

Edit a canonical skill or the canonical resource owner recorded in the [v2 ledger](provenance/skill-sources.json).
Preparation checks reviewed hashes without updating the ledger, preserves canonical files, and generates only
manifests, provenance/hashes, notices, native adapters and needed destination resource copies. Shared references
and license evidence can appear in several independent packages, but only one recorded copy is the editable source.
Unknown paths, missing resources and conflicting ownership fail rather than silently disappearing.

Git contains ready-to-install plugins. `codex plugin add` installs the selected package; it does not run this
repository's Python preparation script. Installed host caches remain copies, not authoring locations. Review
imported guidance against the consuming project's actual authority. Static checks do not guarantee skill discovery,
invocation or model adherence. See the [skill catalog](docs/skill-catalog.md) and [provenance rules](docs/provenance.md).

## Choose a project, not a list of skills

The Copier profile supplies composition; this repository's catalog contains the non-overlapping building blocks.

| Project | Bundle selection |
| --- | --- |
| General Python, automation or reusable robotics module | `common`, `python`; `robotics` only for device/I/O work |
| FastAPI / Litestar API | `common`, `python`, `api-contracts`, `fastapi` / `litestar` |
| React + Vite frontend | `common`, `typescript`, `react-ui` |
| NestJS backend | `common`, `typescript`, `api-contracts`, `nestjs` |
| Next.js full stack | `common`, `typescript`, `react-ui`, `api-contracts`, `nextjs` |
| Rust | `common`, `rust`; async guidance applies only to actual async tasks |
| C++ firmware | `common`, `cpp-firmware` |
| Python API + React / Next.js monorepo | Union of those selections; common cross-package guidance is task-triggered |
| Any project requesting a session reminder | Separately opt in to `session-guidance` and review hook trust |

REST/API contracts are shared, not FastAPI-specific: both FastAPI and Litestar select `api-contracts` plus their
respective framework bundle. Framework skills implement the same wire-contract principles through their own routing,
DI, errors and test APIs. The API-design skill's Python REST asset is an illustrative FastAPI example, not a Litestar
scaffold or a reason to install FastAPI in another framework.

A single Next.js project gets no dedicated Python bundle. In a mixed-language monorepo the host has the union, while
project package routing chooses the relevant instructions for the actual task. Skill metadata can still be visible;
this is not a per-directory model sandbox. Common principles may use another language as an example without adopting
that language, runtime or dependency.

There are **13 bundles and 42 skills**. `session-guidance` has no skills and is never selected automatically.
Monorepo change guidance lives in Common; Rust async guidance lives in Rust. These are task conditions, not more setup options.
Copier bootstrap instructions live in the template's adoption documentation, not in a duplicated skill library.

For visual UI creation, redesign or polish, `react-ui:ui-ux-pro-max` supplies product-appropriate design search/data
alongside `frontend-design`, Impeccable and interface review. Follow the [frontend workflow guide](docs/frontend-workflows.md);
existing product tokens, behavior and framework versions remain authoritative. Nonvisual frontend fixes do not require a redesign.

## Shared methods, project-local contracts

Full development and architecture references are canonical under `plugins/common/references/`; domain references
are owned by their Rust, C++ firmware or robotics plugin. Procedures reach the applicable references locally.
They retain worked cases and decision criteria, not replacement summaries. Source-first
investigation, TDD/SDD and selective DDD are shared procedures; generated product docs retain real structure/specs/ADRs
and local authority, not another methodology manual. Monorepos and single packages retain their own native layout
and package boundaries rather than adopting a required folder tree from this repository.

## Install, activate and update deliberately

Use [host setup](docs/hosts.md) with a local index or the authenticated private Git source. Start with
selected skills only; hooks, MCP, assets and application connectors are not prerequisites. No MCP configuration is bundled.

Plugins enabled globally remain enabled unless the trusted project's configuration explicitly overrides their known
identity. The Copier integration records true/false for every team bundle and leaves unrelated user plugins untouched.
Installing a plugin, enabling it, trusting its hook, fresh-session discovery and correct task invocation are separate
checks. Versions are host-managed, not independent per-repository locks.

## Role adapters, not invented native support

Each bundle has a portable root `plugin.json` for Codex and a `.claude-plugin/plugin.json` adapter. Common also generates
Claude's native `agents/*.md` from the canonical role TOMLs. The inspected Codex clients do **not** register agents from plugins:
the canonical `plugins/common/exports/codex/agents/*.toml` files are explicit optional provisioning artifacts, not auto-loaded roles.
Use built-in Codex agents by default; project-specific specialization belongs at native `.codex/agents/*.toml`.
No generic role bodies are maintained in the template repository. See [host support](docs/hosts.md).

## Maintain and verify

```bash
uv sync --locked
uv run --locked python scripts/build_plugins.py
uv run --locked python scripts/build_plugins.py --check
uv run --locked pytest
```

The maintainer preparation script uses only the Python standard library. It validates inputs and updates generated
metadata/resources; it does not copy or rewrite the canonical skill tree. Neither Git installation nor native
`codex plugin add` runs it on the consumer host. Pytest is a maintainer tool; consumers do not need Python to read the skills
or use the optional shell hook. UI UX Pro Max's optional local search uses Python's standard library and bundled data;
it does not install a Python environment or require the `python` bundle. Do not run product applications or hardware to validate prose.

All use must honor source licensing and access rights. The Git repository is public, but no blanket license is selected
for original material. A new release needs task-specific authorization and license/proprietary-scope review; local
checks do not grant that clearance.

- [Release and rollback](docs/releases.md)
- [Repository structure, hooks and role sources (한국어)](docs/repository-structure.md)
- [Source provenance and transformation](docs/provenance.md)
- [Host configuration and update boundaries](docs/hosts.md)
- [Frontend design and review workflows](docs/frontend-workflows.md)
- [Upstream selection audit](docs/upstream-audit.md)
- [Maintainer contract](AGENTS.md)

## Opt-in agent behavior evaluations

[Agent evals](docs/evals.md) live in `evals/`. `scripts/run_host_evals.py` compares native project skills using existing
Codex authentication and isolated Docker grading; `scripts/run_evals.py` runs both Codex/Claude inside disposable
containers. Both are opt-in. The evaluator tests check the harness offline and never call a model. Existing software
checks remain separate from observed skill reads, behavioral adherence and generated-code outcomes. No model eval is
added to ordinary PR CI, no host authentication is copied, and no automatic A+ score is awarded.
