# Canonical procedure source

This directory owns 41 complete reusable skill trees, portable engineering references, source provenance/licenses
and generic role definitions. Optional reusable forms live in their owning skill assets, not a second templates tree. Imported skill bodies/resources retain their reviewed bytes; two earlier additions are documented
in the [upstream audit](../docs/upstream-audit.md). Copier-specific adoption instructions belong to `project-blueprints`.
There is no template-side skill snapshot or sync operation.

Edit canonical procedures under `.agents/skills`, not generated release artifacts. Follow the
[maintainer contract](../AGENTS.md), [task pointers](.agents/README.md) and [provenance rules](../docs/provenance.md).
The raw tree is not a host installation directory: install closed `plugins/` payloads through the native marketplace.

Raw skill links can denote consuming-project context. The builder's explicit context map converts those to project
lookups; portable engineering/methodology/Rust/C++ references and license/provenance resources are bundled locally. Undeclared
outward paths fail generation. Neither the source layout nor examples override a consuming project's authority.

Generic roles live once in `agents/*.toml`. Generated Claude agents are native adapters; generated Codex exports
require explicit separate provisioning. Codex plugin role auto-loading is not supported in the inspected clients.
