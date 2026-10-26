---
name: typescript-project-structure
description: Choose or review TypeScript library, Node service, and React package boundaries, imports, public exports, and tests. Not a visual-design or framework-migration workflow.
---

# TypeScript project structure

Use the owning package's runtime and published surface to choose the structure, not a generic folder tree.
Read structure choices (look up `docs/structure.md` in the consuming repository; its current project guidance remains authoritative) and [engineering criteria](../../references/engineering.md) when
selecting or changing a package boundary.

## Workflow

1. **Identify the execution contract.** Record library versus application, Node versus browser, module format,
   supported consumers, existing manifest/lock owner, and public entrypoints. A React component library is still a
   library; a browser app must not inherit Node-only imports. A generated baseline is not evidence of the product runtime or supported consumers.
2. **Inspect the import graph.** Find callers, package exports, bundler/test configuration and existing tests before
   moving files. Prefer a small `src/` tree; group React features when they own cohesive UI/state/API behavior.
   Shared code has demonstrated consumers, not merely a convenient `shared` folder name.
3. **Make boundaries real.** Keep library consumers on documented exports; inspect `package.json` `exports`/`types`
   and emitted declarations when a real package exists. Avoid private deep imports and dependency cycles. A
   TypeScript `paths` alias does not rewrite emitted imports or create a runtime/package boundary; runtime,
   bundler and test resolution must agree. Use project references only for actual build/dependency needs.
4. **Preserve runtime semantics.** Inspect the target's compiler/module-resolution settings rather than copying a
   universal `tsconfig`. When implementation is separately authorized, start new packages with strict type checking
   and pin toolchain/package-manager versions, lockfiles, scripts and compatible framework versions together.
   Tightening an existing target needs a scoped migration; do not install or upgrade tools to populate this starter.
5. **Verify the changed surface.** Update imports, exports, tests and docs together. For application code, use the
   declared typecheck/test/build gates and test the consumer-facing boundary; a typecheck alone does not prove
   runtime resolution. For scaffold/guidance work, check paths and metadata only and report runtime checks absent.

## Output

Report the package kind/runtime, dependency direction, public exports, affected callers, selected checks and limits.
For cross-package or wire changes, select the relevant contract workflow from the local catalog (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative)
and account for producer, consumer, authoritative schema and native checks.
For React state/component work, select the relevant `vercel-react-best-practices` or
`vercel-composition-patterns` entrypoint from the catalog (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative), not every frontend skill.
