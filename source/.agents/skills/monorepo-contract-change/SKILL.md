---
name: monorepo-contract-change
description: Coordinate a shared API, schema, event, public package, or native-interface change across monorepo producers and consumers. Not needed for an isolated internal refactor.
---

# Monorepo contract change

One integration owner accounts for the contract and every affected active consumer. A common repository root does
not make languages, runtimes, locks or deployment lifecycles interchangeable.

## Workflow

1. **Map the boundary before edits.** Inspect producers, consumers, fixtures, generated outputs, external consumers,
   package exports and compatibility paths. Name the authoritative schema/source and owner; distinguish wire DTOs
   from domain policy. Mark unknown or unavailable external consumers instead of claiming full compatibility.
2. **Map native environments.** For each package record its language/runtime, native manifest, lockfile, toolchain,
   check commands and release/deployment independence. A root workspace command may orchestrate gates but does
   not replace package-native verification. Rust/Python or Rust/TypeScript interop exists only when an explicit
   FFI, generated binding, CLI or transport contract implements it; co-location provides none.
3. **State the migration.** Record changed fields/semantics, identity, units, errors, ordering, timeouts, versioning,
   backward compatibility, rollout order and rollback as applicable. Use a [small spec](../spec-driven-development/assets/change-spec.md)
   for meaningful changes. Preserve authorized scope and safety authority; do not invent compatibility defaults.
4. **Update the complete slice.** Keep shared schema edits under the integration owner and dependent changes
   sequential. Delegate only independent owned slices. Update producer, every available active consumer, fixtures,
   generators if applicable, public exports and maintained docs together. Never hand-edit generated output without
   inspecting its source, or modify a lockfile through another package's environment.
5. **Verify each side and the seam.** Exercise relevant success/failure/malformed/old-version cases with offline
   fixtures or fakes and native package gates. Cross-language fixture agreement is not executed interoperability.
   Obtain a separate review for cross-package contract changes; report unavailable consumer/native checks and
   require actual integration evidence before claiming compatibility. Scaffold-only work remains static-only.

## Output

Provide a producer/consumer/environment matrix, schema authority, migration and rollback plan, observed native
and boundary evidence, external handoffs and remaining compatibility risks. Do not release, publish or contact
hardware merely because a contract is ready. See [architecture boundaries](../../references/architecture.md) and
[engineering criteria](../../references/engineering.md).
