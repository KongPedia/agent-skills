---
name: rust-best-practices
description: Apply idiomatic Rust ownership, errors, API design, testing and performance guidance when implementing, reviewing or refactoring Rust code; not for prose-only corrections.
---

# Rust Best Practices

> Modified for this repository: metadata uses portable name/description fields; tool permissions are not granted.
> Read the [project Rust adaptation rules](../../references/rust.md#rust-specific-decisions) and [external-guide limits](../../references/rust.md#external-guide-limits) before applying generic examples or commands.

Apply these guidelines when writing or reviewing Rust code. Based on Apollo GraphQL's [Rust Best Practices Handbook](https://github.com/apollographql/rust-best-practices).

## Best Practices Reference

Before reviewing, familiarize yourself with Apollo's Rust best practices. Read only the chapters relevant to the task; independent reading may be parallelized. Reference these files when providing feedback:

- [Chapter 1 - Coding Styles and Idioms](references/chapter_01.md): Borrowing vs cloning, Copy trait, Option/Result handling, iterators, comments, when to extract a function (duplication vs. wrong abstraction)
- [Chapter 2 - Clippy and Linting](references/chapter_02.md): Clippy configuration, important lints, workspace lint setup
- [Chapter 3 - Performance Mindset](references/chapter_03.md): Profiling, avoiding redundant clones, stack vs heap, zero-cost abstractions
- [Chapter 4 - Error Handling](references/chapter_04.md): Result vs panic, thiserror vs anyhow, error hierarchies
- [Chapter 5 - Automated Testing](references/chapter_05.md): Test naming, one assertion per test, snapshot testing
- [Chapter 6 - Generics and Dispatch](references/chapter_06.md): Static vs dynamic dispatch, trait objects
- [Chapter 7 - Type State Pattern](references/chapter_07.md): Compile-time state safety, when to use it
- [Chapter 8 - Comments vs Documentation](references/chapter_08.md): When to comment, doc comments, rustdoc
- [Chapter 9 - Understanding Pointers](references/chapter_09.md): Thread safety, Send/Sync, pointer types

## Quick Reference

### Borrowing & Ownership
- Prefer `&T` over `.clone()` unless ownership transfer is required
- Use `&str` over `String`, `&[T]` over `Vec<T>` in function parameters
- Pass small `Copy` values by value when appropriate; no fixed byte cutoff is a universal rule
- Use `Cow<'_, T>` only when a real borrowed-or-owned API need justifies it

### Error Handling
- Return `Result<T, E>` for fallible operations; avoid `panic!` in production
- Preserve validated invariants and existing error contracts; do not introduce panic paths for expected failures
- Reuse the existing error model; `thiserror`/`anyhow` are optional choices, not mandatory new dependencies
- Prefer `?` operator over match chains for error propagation

### Performance
- Always benchmark with `--release` flag
- Run `cargo clippy -- -D clippy::perf` for performance hints
- Avoid cloning in loops; use `.iter()` instead of `.into_iter()` for Copy types
- Use clear loops or iterators as appropriate; avoid unnecessary intermediate allocations

### Linting
When Rust execution is authorized, use the declared package feature matrix and Clippy gate; do not enable incompatible or hardware features merely to run `--all-features`. Use the owning package README and manifest for its actual commands; a generated baseline is not product correctness evidence.

Key lints to watch:
- `redundant_clone` - unnecessary cloning
- `large_enum_variant` - oversized variants (consider boxing)
- `needless_collect` - premature collection

Use `#[expect(clippy::lint)]` over `#[allow(...)]` with justification comment.

### Testing
- Name tests descriptively: `process_should_return_error_when_input_empty()`
- One assertion per test when possible
- Use doc tests (`///`) for public API examples
- Consider `cargo insta` for snapshot testing generated output

### Generics & Dispatch
- Prefer generics (static dispatch) for performance-critical code
- Use `dyn Trait` only when heterogeneous collections are needed
- Box at API boundaries, not internally

### Type State Pattern
Encode valid states in the type system to catch invalid operations at compile time:
```rust
struct Connection<State> { /* ... */ _state: PhantomData<State> }
struct Disconnected;
struct Connected;

impl Connection<Connected> {
    fn send(&self, data: &[u8]) { /* only connected can send */ }
}
```

### Documentation
- `//` comments explain *why* (safety, workarounds, design rationale)
- `///` doc comments explain *what* and *how* for public APIs
- Every `TODO` needs a linked issue: `// TODO(#42): ...`
- Enable `#![deny(missing_docs)]` for libraries

## Pinned Google style reference

For relevant Rust style or API decisions, consult the selected sections of the local [Google Rust Style Guide](references/google-rust-style-guide.md). Its codebase-specific rules are not blanket authority for the owning crate; the project adaptation rules linked above govern applicability. Read only the sections needed for the task.

Source notices are preserved in the [Apollo MIT license](references/apollo-LICENSE.md), [Google license](references/google-styleguide-LICENSE.md) and [Google attribution and licensing declaration](references/google-styleguide-licensing.md). These are text references, not installed plugins or executable tools.
