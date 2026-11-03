# Canonical provenance and closed plugin payloads

The canonical library began at the historical `source/.agents` path with a reviewed Project Blueprints
skill/resource snapshot. It later used `source/skills`; those paths are retained only in historical derivation
evidence. The current 42 skill trees live once under their owner `plugins/<bundle>/skills/` directories.
The initial extraction was uncommitted; do not invent a Git revision for it. Historical byte-equality counts
are not a current blanket preservation claim after later reviewed adaptations.

Copier bootstrap instructions belong to `project-blueprints`. Generated products keep real contracts, commands,
specs and ADRs, not copied shared skill bodies or methodology manuals.

## Canonical inputs and generated destinations

[`provenance/skill-sources.json`](../provenance/skill-sources.json) is the central v2 ledger. Its `local` file paths
and source license pointers are repository-relative, not relative to this document or a removed source folder.
Imported records retain their immutable repository, revision, upstream path/hash and existing derivation evidence.
The local `sha256` records independently reviewed canonical bytes. Preparation checks it; preparation does not
update it to approve whatever it finds.

Canonical inputs have explicit owners:

- Every skill body, asset, script and data file belongs to one `plugins/<bundle>/skills/<skill>/` tree.
- Common owns shared engineering, development and architecture references. Rust, C++ firmware and Robotics own
  their respective domain references. The ledger identifies each canonical reference path.
- Each imported license/NOTICE has one designated canonical plugin owner. Other packages receive required copies.
- Generic model-free role TOMLs are canonical at `plugins/common/exports/codex/agents/*.toml`. Common's Claude
  `agents/*.md` are generated adapters. The TOMLs are optional explicit Codex provisioning artifacts, not evidence
  that Codex automatically registers plugin roles.
- `plugins/session-guidance/hooks/session-start.sh` is the canonical printf-only advisory. Its generated
  `hooks/hooks.json` uses native default discovery; opt-in activation and hook trust remain separate.

Edit the recorded canonical owner, not another bundle's generated reference/license copy, host cache or metadata.
All canonical inputs, including promoted references, roles and the hook, need reviewed local hash evidence.
Original organization-authored resources retain truthful origin records without invented upstream hashes or licenses.

## Preparation is not a second skill tree

`scripts/build_plugins.py` retains the maintainer preparation and `--check` interface. It performs finite,
explicit work:

1. Validate catalog ownership, canonical paths, reviewed hashes and source/license metadata before mutation.
2. Read canonical skill trees without rewriting them. Same-bundle links stay local; cross-bundle skill links use
   stable `bundle:skill` identities and selection notes. Project-context instructions are consuming-repository
   lookups, not assertions that a particular template layout exists.
3. Resolve shared resources from their recorded canonical owner, never from an old generated destination. Include
   needed copies in each independent package and adapt their links for that destination bundle.
4. Generate manifests, per-plugin provenance/hashes, notices, composition notes, marketplace indexes, Claude role
   adapters and optional hook configuration. Preserve every recorded required license/NOTICE byte.
5. Validate the complete staged package: missing resources, undeclared outward paths, absolute local links,
   conflicting owners and symlinks fail. Installed Markdown must stay inside its own plugin root.
6. Update only explicit generated destinations. Canonical input paths and generated write paths must be disjoint,
   including canonical files inside `references/`, `licenses/`, `exports/` and `hooks/`. Never replace the whole
   `plugins/` tree or use artifact hashes as deletion authority. Per-file atomic writes are not a whole-tree
   transaction; verify the complete result before publication.

A temporary staged payload may contain copies for validation or installation testing. It is not another
Git-tracked authoring tree. `--check` checks prepared metadata/resource consistency without writing files.

Markdown links inside fenced code examples remain examples, not resource declarations. External documentation
links remain external; local closure checks do not establish availability or correctness of every remote URL.

## Separate hashes for separate claims

Each package's generated `provenance.json` uses plugin-relative `local` and license paths, unlike the central
ledger's repository-relative canonical paths. It filters selected source/license records and records:

- `upstream_sha256`: original upstream bytes at the immutable revision;
- `source_sha256`: reviewed canonical local bytes;
- `payload_sha256`: actual bytes in that installed package;
- `canonical_source`: the actual repository-relative canonical path.

Source and payload hashes can be equal for a canonical skill installed without transformation. A shared reference
can have different canonical and destination hashes after cross-bundle link adaptation. Existing derivation
repository/revision/path/hash values stay historical; moving the current file does not rewrite its origin.

`artifact-hashes.json` lists every actual package file's SHA-256 except itself, including canonical files. It detects
stale or modified package bytes; it is not a write/deletion allowlist. Hash agreement does not prove safe source
selection, runtime loading, model compliance or product safety. Every installed local resource is package-local;
no installed Markdown link relies on another plugin's cache directory or the provider Git root.

## Licensing and distribution boundary

Local/private distribution needs no public directory, but must respect source licenses, attribution and team access
rights. Imported sources retain their individual notices. Some original team procedures/resources do not have a
selected public license. Do not fabricate a root license or manifest-wide MIT claim. Public publication needs
separate human review of original material, upstream obligations, trademarks and proprietary scope. Passing local
checks is not legal/license clearance.

## Canonical additions and roles

The full upstream `domain-modeling` and `python-type-safety` directories extended the earlier inventory to 41.
Their immutable raw hashes, narrow adaptations and licenses remain recorded. Python type safety has a distinct
source identity/revision; earlier wshobson imports are not silently reattributed.

UI UX Pro Max extends the inventory to 42 under `react-ui`. Its adapted procedure, references and standard-library
Python search/data retain immutable upstream and reviewed local hashes plus MIT evidence. Upstream installers,
host plugin/hook setup and platform templates are excluded. Suggestions do not override product design or native
toolchains; persistence needs explicit write scope. Historical behavior-evaluation inputs and results are unchanged.
The local runtime adaptation propagates data-read failures instead of silently recommending defaults and rejects
symlinked managed output paths before persistence. Its reviewed local hashes differ from the pinned upstream hashes.

Shared development, architecture and robotics worked references retain their useful cases, with consuming-project
lookups and layout examples. They are canonical under their owning plugin and included where needed, not independently
maintained in the template. These references can affect guidance even when an imported skill's bytes are unchanged.

## Reusable artifact forms

Common owns optional task/change forms in existing skill `assets/` directories. Docs Sync owns one combined
package/folder README guide; Domain Modeling retains Matt Pocock's existing `ADR-FORMAT.md`, not a second ADR form.
Existing project formats and filled records remain authoritative; assets do not require a document for every task.

`authored_skills` records original procedures and assets; `authored_resources` records original supporting inputs.
Both retain reviewed local hashes without invented upstream hashes or licenses. Canonical skill files and assets
appear in installed `authored_files`; non-skill supporting inputs and generated adapters appear in
`supporting_resources`. Imported files remain in `files` and retain their original upstream hashes. The former
`.agents/templates` mirror was removed; neither blueprint sources nor new products keep another form library.
