# Rust decision reference

Use this reference with the relevant Rust skills and [engineering criteria](engineering.md). Use the owning package's actual
Cargo manifest, feature/target matrix, toolchain and lifecycle contracts. A generated minimal crate or imported reference
is not proof of product correctness, supported external consumers or deployed behavior.

## Rust-specific decisions

- Choose library versus executable responsibility first. Cargo's conventional `src/lib.rs`, `src/main.rs`, `src/bin/`
  and integration `tests/` inform a real crate; empty skeleton directories do not become targets without source/manifests.
- State supported Rust/edition, features, target platforms and dependencies when implementation is authorized. Keep
  `Cargo.toml`, lockfile policy and any `rust-toolchain.toml` aligned with actual consumers. A workspace shares selected
  configuration/resolution, not one implicit runtime or release lifecycle.
- Design around ownership and useful public types. Prefer borrowing where it expresses the lifetime correctly, but
  do not mechanically replace owned values or `clone` without caller/performance evidence. Use traits when they clarify
  a real boundary; concrete collaborators are valid.
- Keep malformed/untrusted input fallible and errors meaningful at the boundary. `unwrap`, `expect`, panic and unsafe
  require context-specific justification; an imported sample is not evidence that a production path is safe.
- Async is a workload decision. Tokio, another runtime or synchronous I/O must follow the owning package; do not add
  Tokio to every crate. Spawned tasks need explicit ownership, cancellation, backpressure and shutdown semantics.
- PyO3/FFI is optional, not implied by a mixed Python/Rust repository. An actual native boundary must define ABI/binding
  generation, supported interpreters/targets, packaging, error/ownership rules and both sides' verification.

## External guide limits

`rust-best-practices`, `rust-async-patterns` and `deprecation-and-migration` provide selective guidance, not approved
application scaffolds. Read the relevant branch only. Keep any executable snippets, package commands, runtime assumptions
and dependencies under source review; do not execute them merely to validate a document.

Source repositories may target a specific SDK, transport, Python binding, async runtime or hardware environment. Those
contracts do not carry into this neutral starter. Match examples to the adopted package's compiler/features, actual
public surface and safety authority. Generic allocation, style, trait or folder recommendations are not hard gates.

For guidance-only changes, verify paths, metadata, licenses/provenance and whitespace. Once a real crate exists, select
its declared feature/target-aware checks, typically formatting, linting, unit/integration and build/documentation checks
where applicable. Record what actually ran; the presence of `Cargo.toml` or a workspace is not passing evidence. Native
consumer checks remain separate from another language's test suite. No network, deployment or hardware success is implied.

## Module design and migration

Module visibility and public exports are part of the API, not just file organization. Inspect downstream imports,
feature-gated paths, examples and tests before moving a module. Keep private implementation details private; splitting
one file does not require exposing every new module or adding one forwarding layer per file.

For a public rename/removal or behavior change, identify affected consumers and the compatibility commitment. Decide
whether a deprecated re-export/adapter, staged migration or explicit breaking release is appropriate; do not invent a
grace period or promise compatibility for unknown external users. Preserve errors and resource semantics through any
adapter. Document removal conditions and test old/new paths while both are supported.

For cross-package or cross-language changes, use
the relevant cross-package workflow from the local catalog (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative). Update authoritative source, generated binding
inputs if any, available consumers and fixtures together. Byte-equal fixtures alone do not prove executed interop; do
not update a sibling repository or publish a crate without task authorization. Record rollback and unavailable checks.

Use the official [Cargo package layout](https://doc.rust-lang.org/cargo/guide/project-layout.html) and
[workspace reference](https://doc.rust-lang.org/cargo/reference/workspaces.html), plus the selected Rust skills.
