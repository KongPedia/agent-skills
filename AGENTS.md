# Agent Skills maintainer contract

This repository owns plugin-native reusable skills, optional advisory hooks, and prepared portable plugin releases. It does not
own consuming projects' code layouts, commands, domain contracts, credentials, trust or hardware permissions.

## Authority and ownership

- Follow the latest user request and consuming project authority. Do not publish, commit, tag, add remotes, install
  plugins or change host settings without the corresponding task-specific authorization and applicable review.
- Existing release history is not authorization for new commits, pushes, tags, publication or host changes.
  Obtain corresponding task-specific authority; Git/publication work belongs to the assigned integration owner.
  Shared maintainer docs stay generic. Keep consumer-specific migration receipts in that consumer or external task evidence,
  not in this reusable provider; preserve accurate upstream/derivation provenance even when it names an originating repository.
- `catalog.json` owns stable bundle identities, the release version and exactly one owner per reusable skill.
  `requires` documents composition; it is not a host dependency schema or automatic installation mechanism.
- Canonical procedures/resources live once at `plugins/<bundle>/skills/<skill>`. The v2 ledger at
  `provenance/skill-sources.json` records immutable upstream/derivation evidence and independently reviewed local hashes.
  Bootstrap/adoption instructions belong to the Copier repository documentation, not a duplicated skill here.
- Canonical shared references and license/NOTICE files have one plugin owner declared by the ledger. Other bundles
  receive generated closed-package copies. Edit the recorded owner, not a destination copy.
- Canonical generic role TOMLs live in `plugins/common/exports/codex/agents`; Common's Claude `agents/*.md` are generated
  adapters. The TOMLs are explicit provisioning artifacts, not plugin agent auto-registration in the inspected clients.
- `scripts/build_plugins.py` validates canonical inputs and prepares only declared generated metadata, adapters and
  destination resources, including both marketplace indexes. It must never overwrite/delete canonical inputs or
  replace the whole `plugins/` tree. Never hand-edit generated destinations or auto-approve new canonical hashes.
  The template repository consumes stable plugin identities, not a skill snapshot; do not edit it during sibling tasks.
- Read the exact relevant `plugins/common/skills/writing-for-agents/SKILL.md`,
  `plugins/common/skills/codebase-design/SKILL.md`, `plugins/common/skills/test-driven-development/SKILL.md` and
  `plugins/common/skills/verification-before-completion/SKILL.md` for substantive changes. Project-context paths
  are consuming-repository lookups, not instructions to assume a particular template layout exists here.
- Preserve other workers' changes. Keep shared catalog/build integration sequential; delegate only bounded owned files.
- Native Copier is the creation interface: reviewed `copy --trust` may install selected Codex plugins, while
  `--skip-tasks` renders only. Do not add a custom creation CLI, automatic consent or strict existing-path guarantees.
- For a missing marketplace/plugin error, explain one-time reviewed registration and preserve the native error.
  Never automatically retarget an existing same-name source or treat URL/ref settings as cached-payload proof.

## Changes and evidence

- Inspect source, consumers, fixtures, metadata and update behavior before editing. Keep procedure bodies and useful
  resources, not summaries. Imported changes require immutable source/derivation/upstream hashes and reviewed local hashes.
- Project-owned paths are explicit consuming-repository lookups. Same-bundle resources stay local; cross-bundle skill
  links use stable identities plus selection notes. Preparation resolves shared resources from their registered canonical
  owners, never from an old destination copy. Unknown outward paths, missing resources and symlinks fail checks.
- Include each selected imported source's license evidence. Do not invent a blanket license for original material;
  a public release needs a separate license audit and decision.
- Run `uv run --locked pytest` and `uv run --locked python scripts/build_plugins.py --check`. Generator behavior needs
  meaningful failing regression coverage first. Prose-only work uses metadata, reference, license/hash and diff checks.
- `plugins/session-guidance/hooks/session-start.sh` is the canonical, separate opt-in SessionStart advisory:
  printf only, no scans, network, tests, application,
  credentials, permission mutation or hardware. No manifest hooks override; default `hooks/hooks.json` discovery only.
- Do not copy caches, personal configuration, auth, sessions or machine trust. Test host installation only with disposable
  HOME/CODEX_HOME, and distinguish install/config checks from fresh-session discovery/invocation/adherence.
- Report observed checks and omissions. Never present static checks or model instruction text as enforcement, deployment,
  external compatibility or physical validation.
