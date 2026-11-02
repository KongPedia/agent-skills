# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

## Dependency categories

When assessing a candidate for deepening, classify its dependencies. The category determines how the deepened module is tested across its seam.

### 1. In-process

Pure computation, in-memory state, no I/O. Consider merging only when the responsibilities cohere; characterize behavior first and test through the resulting interface. An adapter is not needed merely to merge pure computation.

### 2. Local-substitutable

Dependencies that have local test stand-ins (PGLite for Postgres, in-memory filesystem). A suitable existing stand-in can support deepening; check its behavioral fidelity and owning environment first. The deepened module is tested with the stand-in running in the test suite. The seam is internal; no port at the module's external interface.

### 3. Remote but owned (Ports & Adapters)

Your own services across a network boundary (microservices, internal APIs). Reuse an existing **port** (interface) at the seam, or introduce one only when the responsibility warrants it. The deep module owns the logic; the transport is injected as an **adapter**. Tests use an in-memory adapter. Production uses an HTTP/gRPC/queue adapter.

Recommendation shape: *"Define a port at the seam, implement an HTTP adapter for production and an in-memory adapter for testing, so the logic sits in one deep module even though it's deployed across a network."*

### 4. True external (Mock)

Third-party services (Stripe, Twilio, etc.) you don't control. The deepened module takes the external dependency as an injected port; tests provide a mock adapter.

## Seam discipline

- **Responsibility before adapter counts.** Production plus a test fake can justify substitution, but a single implementation may still require isolation for I/O, lifecycle or safety. Avoid pass-through layers, not necessary ownership boundaries.
- **Internal seams vs external seams.** A deep module can have internal seams (private to its implementation, used by its own tests) as well as the external seam at its interface. Don't expose internal seams through the interface just because tests use them.

## Testing strategy: prove equivalent coverage before removing duplication

- Inventory old assertions before consolidation. Remove only proven duplicate tests after replacement coverage passes and preserves failure localization; never delete low-level or safety regressions merely because broader interface tests exist.
- Prefer new behavior tests at the deepened module's interface; retain codec, malformed-input, cancellation, shutdown and integration tests at the level where their failures remain observable.
- Assert observable outcomes where practical; focused internal invariants remain valid when they protect behavior or safety unavailable through the public seam.
- Tests should generally survive internal refactors. A changed test is a review signal, not proof it was invalid: check whether contracts, safety invariants or test access genuinely changed.
