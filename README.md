# Konglabs Agent Skills

One versioned organization source for reusable engineering skills and **optional** advisory hooks. Language and
framework bundles are folders in this repository, not separate repositories and not one repository per combination.

**Private first-release destinations:** [KongPedia/agent-skills](https://github.com/KongPedia/agent-skills) and
[KongPedia/project-blueprints](https://github.com/KongPedia/project-blueprints), with matching `v0.1.0` tags/releases.
Private creation/push/release is authorized; public publication is not. A marketplace is a plugin index, not a public
store: this checkout or the authenticated private Git source works without a directory listing.

## First-run recovery: plugin not found

If Codex reports `plugin X not found in marketplace konglabs-agent-skills`, first check whether the reviewed source
has been registered on this host. If not, register it **once**:

```bash
codex plugin marketplace add ~/Desktop/workspace/konglabs/agent-skills
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

```text
catalog.json                       # One bundle owner per skill; version and composition metadata
source/.agents/skills/             # Canonical complete procedures and resources; edit these
source/.agents/skill-sources.json   # Immutable upstream/source provenance and local source hashes
source/.agents/licenses/           # Imported license evidence
source/.agents/references/         # Canonical shared engineering/methodology/worked references
source/agents/*.toml               # Canonical model-free generic roles
hooks/session-start.sh             # Canonical optional printf-only advisory
scripts/build_plugins.py           # Standard-library deterministic builder and --check
plugins/<bundle>/                  # Generated, closed installed payloads; do not hand-edit
.agents/plugins/marketplace.json   # Generated Codex marketplace adapter
.claude-plugin/marketplace.json    # Generated Claude marketplace adapter
```

Generated payloads are intended Git-managed release artifacts, not a second hand-maintained library. The builder preserves full
procedure bodies and resources, rewrites only declared location-dependent links, retains licenses, and records
upstream/source/payload hashes separately. Unknown outward references fail rather than silently disappearing.

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

A single Next.js project gets no dedicated Python bundle. In a mixed-language monorepo the host has the union, while
project package routing chooses the relevant instructions for the actual task. Skill metadata can still be visible;
this is not a per-directory model sandbox. Common principles may use another language as an example without adopting
that language, runtime or dependency.

There are **13 bundles and 41 skills**. `session-guidance` has no skills and is never selected automatically.
Monorepo change guidance lives in Common; Rust async guidance lives in Rust. These are task conditions, not more setup options.
Copier bootstrap instructions live in the template's adoption documentation, not in a duplicated skill library.

## Shared methods, project-local contracts

Full development, architecture and robotics references live under `source/.agents/references/`, reached from their
common/robotics procedures. They retain worked cases and decision criteria, not replacement summaries. Source-first
investigation, TDD/SDD and selective DDD are shared procedures; generated product docs retain real structure/specs/ADRs
and local authority, not another methodology manual. Monorepos use root `apps/` and `packages/`; each package keeps its
native `src/`. Single packages retain their native layout.

## Install, activate and update deliberately

Use [host setup](docs/hosts.md) with a local index or the authenticated private Git source. Start with
selected skills only; hooks, MCP, assets and application connectors are not prerequisites. No MCP configuration is bundled.

Plugins enabled globally remain enabled unless the trusted project's configuration explicitly overrides their known
identity. The Copier integration records true/false for every team bundle and leaves unrelated user plugins untouched.
Installing a plugin, enabling it, trusting its hook, fresh-session discovery and correct task invocation are separate
checks. Versions are host-managed, not independent per-repository locks.

## Role adapters, not invented native support

Each bundle has a portable root `plugin.json` for Codex and a `.claude-plugin/plugin.json` adapter. Common also exports
Claude's native `agents/*.md` from the canonical role TOMLs. Codex currently does **not** register agents from plugins:
its generated `exports/codex/agents/*.toml` are explicit optional provisioning artifacts, not auto-loaded roles.
Use built-in Codex agents by default; project-specific specialization belongs at native `.codex/agents/*.toml`.
No generic role bodies are maintained in the template repository. See [host support](docs/hosts.md).

## Maintain and verify

```bash
uv sync --locked
uv run --locked python scripts/build_plugins.py
uv run --locked python scripts/build_plugins.py --check
uv run --locked pytest
```

The builder has no runtime dependencies. Python and pytest are maintainer tools only; a Next.js consumer does not
need Python to use the skills or the optional shell hook. Do not run product applications or hardware to validate prose.

Private/team use still must honor source licensing and access rights. Public publication, if later requested, needs
original-material license selection and a secret/proprietary-scope audit; local checks do not grant that clearance.

- [Release and rollback](docs/releases.md)
- [Source provenance and transformation](docs/provenance.md)
- [Host configuration and update boundaries](docs/hosts.md)
- [Upstream selection audit](docs/upstream-audit.md)
- [Maintainer contract](AGENTS.md)
