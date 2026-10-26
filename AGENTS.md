# Agent Skills maintainer contract

This repository owns reusable skills, optional advisory hooks, and generated portable plugin releases. It does not
own consuming projects' code layouts, commands, domain contracts, credentials, trust or hardware permissions.

## Authority and ownership

- Follow the latest user request and consuming project authority. Do not publish, commit, tag, add remotes, install
  plugins or change host settings without the corresponding authorization. Public publication is not yet authorized.
- Existing release history is not authorization for new commits, pushes, tags, publication or host changes.
  Obtain corresponding task-specific authority; Git/publication work belongs to the assigned integration owner.
  Shared maintainer docs stay generic. Keep consumer-specific migration receipts in that consumer or external task evidence,
  not in this reusable provider; preserve accurate upstream/derivation provenance even when it names an originating repository.
- `catalog.json` owns stable bundle identities, the release version and exactly one owner per reusable skill.
  `requires` documents composition; it is not a host dependency schema or automatic installation mechanism.
- Canonical generic roles live in `source/agents`; Claude adapters and optional Codex exports are generated, not two authored copies. Codex plugin role auto-loading is not supported in the inspected clients.
- Canonical procedures/resources live in `source/.agents/skills`; pinned sources, upstream/local hashes and licenses
  live beside them. Bootstrap/adoption instructions belong to the Copier repository documentation, not a duplicated skill here.
- `scripts/build_plugins.py` owns deterministic generation of `plugins/` and both marketplace adapters. Never hand-edit
  generated plugin files. The template repository consumes stable plugin identities, not a skill snapshot; do not edit it during sibling tasks.
- Read the exact relevant `source/.agents/skills/writing-for-agents/SKILL.md`, `codebase-design/SKILL.md`,
  `test-driven-development/SKILL.md` and `verification-before-completion/SKILL.md` for substantive changes. Source
  project-context paths are declared lookups, not instructions to assume a particular template layout exists here.
- Preserve other workers' changes. Keep shared catalog/build integration sequential; delegate only bounded owned files.
- Native Copier is the creation interface: reviewed `copy --trust` may install selected Codex plugins, while
  `--skip-tasks` renders only. Do not add a custom creation CLI, automatic consent or strict existing-path guarantees.
- For a missing marketplace/plugin error, explain one-time reviewed registration and preserve the native error.
  Never automatically retarget an existing same-name source or treat URL/ref settings as cached-payload proof.

## Changes and evidence

- Inspect source, consumers, fixtures, metadata and update behavior before editing. Keep procedure bodies and useful
  resources, not summaries. Imported changes require immutable source/derivation/upstream hashes and reviewed local hashes.
- Project-owned paths are explicit consuming-repository lookups. Same-bundle resources stay local; cross-bundle skill
  links become stable identities plus selection notes. Unknown outward paths, missing resources and symlinks fail builds.
- Include each selected imported source's license evidence. Do not invent a blanket license for original material;
  a public release needs a separate license audit and decision.
- Run `uv run --locked pytest` and `uv run --locked python scripts/build_plugins.py --check`. Generator behavior needs
  meaningful failing regression coverage first. Prose-only work uses metadata, reference, license/hash and diff checks.
- `session-guidance` is a separate opt-in SessionStart advisory: printf only, no scans, network, tests, application,
  credentials, permission mutation or hardware. No manifest hooks override; default `hooks/hooks.json` discovery only.
- Do not copy caches, personal configuration, auth, sessions or machine trust. Test host installation only with disposable
  HOME/CODEX_HOME, and distinguish install/config checks from fresh-session discovery/invocation/adherence.
- Report observed checks and omissions. Never present static checks or model instruction text as enforcement, deployment,
  external compatibility or physical validation.
