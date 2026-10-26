# Source provenance and closed payloads

`source/.agents` began with the reviewed Project Blueprints reusable skill/resource snapshot; Copier bootstrap
instructions are not a shared skill. The canonical inventory is now 41 procedures with retained immutable upstream and
derivation records. The initial extraction was uncommitted; do not invent a source Git revision. Historical extraction
byte-equality counts are not a current blanket preservation claim after later recorded changes.

Existing imported skill trees were not rewritten when the full development, architecture and robotics references moved
into `source/.agents/references/`. Three authored skill routing links changed and their local hashes were recorded.
The complete shared references remain canonical here; generated products keep local contracts, not copied manuals.

## One source, generated adapters

Edit canonical source only, review its existing upstream/local changes and update the recorded local SHA-256 when
that adaptation changes. Keep the immutable original upstream hash and derivation history. A source hash mismatch
stops the build. Version/bundle ownership lives in `catalog.json`; plugin payloads and marketplace JSON are regenerated.

The builder performs a finite, explicit transformation:

1. Copy every file in each selected skill tree; never replace a procedure with a summary.
2. Keep same-bundle skill links local and include their actual resource targets.
3. Replace cross-bundle skill links with stable `bundle:skill` identities and a selection note. The target procedure
   stays under its one canonical owner; dependencies are explicit composition metadata, not silently installed.
4. Replace declared project-context links—README, routing, local structure/specs/ADRs and other
   declared contextual lookups—with explicit lookups in the **consuming repository**. They do not assert every project
   has that file; inspect current authority and native manifests instead of borrowing template assumptions.
5. Include canonical engineering/Rust/C++ and full development/architecture/robotics references when reached by the
   selected procedures. Close their packaged references with the same rules; do not replace worked cases with summaries.
6. Include every recorded license/NOTICE file for each selected imported source, preserving bytes. Reject undeclared outward references,
   missing resources, absolute local paths and symlinks. Preflight every managed destination and its ancestors,
   including existing plugin-tree nodes, before reading or replacing output; reject wrong path types as well.

Markdown links inside fenced code examples remain examples, not resource declarations. External documentation links
remain external; this build checks local resource closure, not current availability or correctness of every remote URL.

## Separate hashes for separate claims

Each generated `provenance.json` filters the selected source/license records and records:

- `upstream_sha256`: original upstream bytes at the immutable upstream revision;
- `source_sha256`: reviewed canonical local bytes before portable path rewriting;
- `payload_sha256`: actual installed bytes after transformation;
- `canonical_source`: the traceable source path; existing derivation records stay intact.

`artifact-hashes.json` lists every actual payload file's SHA-256 except itself. It detects stale/modified artifacts,
not malicious source selection, runtime loading, model compliance or product safety. License evidence and source
metadata are payload-local; no installed Markdown link relies on another plugin's cache directory or on this Git root.

## Licensing and distribution boundary

Local/private distribution needs no public directory, but still must respect source licenses, attribution and team
access rights. Imported sources retain their individual notices. Some original team procedures/resources do not yet
have a selected public license. No root license or manifest-wide MIT claim is fabricated. Before public publication,
a human must review original material licensing, upstream attribution/notice obligations, trademarks and information
that should not be public. Local passing tests are not a legal/license clearance.

## Current canonical additions and roles

The full upstream `domain-modeling` and `python-type-safety` directories extend the original inventory to 41; pinned
raw hashes, local adaptations and licenses are recorded beside the bodies. The Python addition has a distinct source
identity/revision, so earlier wshobson imports are not silently reattributed. The public source audit explains exclusions.
Engineering/Rust/C++ and the full shared development/architecture/robotics references are canonical here and packaged
as needed, not independently maintained in the template or copied into generated project docs.
Four model-free generic role TOMLs have one canonical source and generated Claude/native-Codex-export adapters.
Exported role configuration is not evidence of Codex plugin agent registration.

## Shared documentation versus product artifacts

Complete development, architecture and robotics worked references moved from the template into canonical
`source/.agents/references`. They retain their useful examples, with updated consuming-project links and root
`apps`/`packages` layout examples. Common links development/architecture; Robotics links its own example.
These are generated closed payload resources with source/payload hashes, not copied project methodology documents.
Project specs, ADRs, ownership, commands and local policy remain project-owned artifacts.


## Reusable artifact forms

Common owns optional task/change forms under their existing skill `assets/` directories. Docs Sync owns one combined
package/folder README guide; Domain Modeling retains Matt Pocock's existing `ADR-FORMAT.md`, not a second ADR form.
These are shared resources, not consuming-project lookups. Existing project formats and filled product records remain
authoritative; assets do not require a document for every task or folder.

`authored_skills` records original procedure files and their assets; `authored_resources` separately records original
team assets attached to imported skills. Both require reviewed source hashes. They generate `authored_files` provenance
without invented upstream hashes or licenses. Imported entrypoint adaptations retain their original upstream hashes.
The former source `.agents/templates` mirror is removed; neither blueprint sources nor new products keep form copies.
