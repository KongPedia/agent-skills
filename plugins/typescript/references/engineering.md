# Engineering criteria

Use these criteria for package design, implementation and substantive review. They complement the
task workflow (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative); the actual task, applicable `AGENTS.md` and owning package's declared contracts take
precedence. They apply to the template source and generated projects alike. The project README (look up `README.md` in the consuming repository; its current project guidance remains authoritative)
and native manifests establish current packages and commands; files do not prove tool enforcement or model adherence.

## Responsibility and dependency boundaries

Start with the owning package and its actual callers. A small package may keep related policy and orchestration in
one module; split when responsibilities have independent reasons to change, different dependencies or awkward test
setup. Directory count is not a measure of architecture quality. See the
[architecture guide](architecture.md) for repository package groups, native packages and a coherent worked use case.

| Responsibility, when present | Owns | Keep outside |
| --- | --- | --- |
| Composition/entrypoint | Configuration, wiring, resource startup/shutdown | Domain decisions hidden in startup code |
| API/CLI/transport boundary | Input validation, admission, error/response translation | Business policy and direct storage decisions |
| Use case/service | A named operation and coordination of concrete collaborators | Transport framework objects and connection plumbing |
| Domain/policy | Vocabulary, invariants and deterministic decisions | Network, database and UI framework dependencies |
| Repository/storage | Query, persistence and consistency semantics | HTTP/UI response mapping |
| Adapter | Bounded external I/O and protocol translation | A second authoritative business policy |
| UI feature | Rendering, interaction and presentation state | Duplicated server authority or fabricated completion |
| Shared contract | Reused public data/API semantics | Imports back into consuming applications |

Use these as responsibilities, not mandatory folders or a required Clean Architecture rewrite. Composition can inject
small concrete collaborators; abstract base classes, traits, DI frameworks, generic repositories, CQRS and event sourcing
need a demonstrated benefit. Select domain-heavy patterns for real invariants and lifecycle ownership, not every CRUD API.

## Common design and clean-code decisions

These criteria carry applicable design-pattern, SRP, clean-code and best-practice guidance across languages; they are
not limited to one imported author or source family. Read the exact applicable procedures through the catalog.

| Decision | Concrete action and reason |
| --- | --- |
| KISS/YAGNI | Solve the authorized outcome with an existing utility, native feature or a named function before a framework; omit hypothetical options. |
| SRP/separation of concerns | List reasons to change. Separate policy, delivery mapping and I/O when they vary independently or force broad test setup; do not split by line count. |
| DRY | Centralize duplicated knowledge/contract authority that can diverge, not every similar expression. A third copy is a useful signal, not a required wait when divergence already causes bugs. |
| Composition | Inject a small concrete I/O collaborator or callable instead of constructing external clients inside policy. Keep cleanup ownership explicit; avoid nested forwarding wrappers. |
| Port/adapter | Name the real external/substitution contract, including errors and lifetime. A concrete collaborator or structural interface can suffice; do not require an ABC/trait for every call. |
| Strategy/open extension | Use a function or explicit mapping for real variants sharing one contract. Add a strategy only when behavior actually varies; test existing and new variants through that contract. |
| Domain modeling | Define vocabulary, state owner and invariants before entities/aggregates. A bounded context is a semantic ownership boundary, not a folder; DTO sharing does not transfer policy authority. |
| Readability | Prefer domain names, explicit inputs/results and clear guards/loops. Comments explain a non-obvious constraint or reason; do not narrate obvious code or hide errors to shorten it. |

An interface includes ordering, required configuration, errors and safety/lifecycle semantics, not only a type signature.
Deep modules hide useful complexity for callers and keep fixes local. Deleting a wrapper that merely forwards is often
better than giving it another interface. Keep one canonical contract instead of caching it in many handlers/READMEs.
The [report-export example](architecture.md#worked-example-report-export) shows when a seam or strategy earns
its cost and how a spec becomes invariants and tests; it does not prescribe an application feature.

## Naming, interfaces and package ownership

| Language/surface | Naming convention, subordinate to established public contracts |
| --- | --- |
| Python | Import modules/functions/variables `snake_case`; classes/types `PascalCase`; constants `UPPER_SNAKE_CASE`; tests `test_<behavior>`. Distribution names and import names are separate decisions. |
| TypeScript | Functions/variables `camelCase`; types/classes/components `PascalCase`; hooks `use<Role>`; component files follow the package convention, e.g. `ExportButton.tsx`; tests describe the expected behavior. |
| Rust | Modules/functions/variables and test functions `snake_case`; types/traits/variants `PascalCase`; constants `SCREAMING_SNAKE_CASE`. Preserve the distinction between Cargo package names and crate/module identifiers. |
| Wire/schema/CLI | Keep established field names, flags, enum values and units stable even when they differ from local language style; version/migrate explicit changes. |

- Name domain actions, predicates, units and identities explicitly. Keep wire names stable even when local style differs;
  test conversions instead of silently renaming a contract. Use `is_ready`/`isReady`, `timeout_ms`/`timeoutMs`, and distinct
  request/device/report identities where applicable. Avoid a general `utils`, `manager` or `data` name when the role is known.
- Define a package's supported public surface. Python does not require blanket `__all__`; TypeScript aliases do not
  establish exports/runtime resolution; Rust file visibility is not the same as a stable public crate API.
- Preserve package-native manifests, toolchains and lock ownership. Shared schemas have one authority and every active
  consumer is updated together. A mixed-language workspace does not imply FFI, generated bindings or one environment.
- Match examples to the target version, runtime and framework. Do not upgrade dependencies, switch module formats or
  add a package manager solely to follow a skill. Pin toolchain/formatter/linter versions in the actual owning package;
  new TypeScript packages start strict, while tightening an existing target needs a scoped compatibility migration.

## Python configuration and type boundaries

Validate settings once at composition/startup: required values, units/ranges, finite timeouts, bounded queue sizes and
allowed endpoints. Keep secrets out of logs and preserve the owning package's existing configuration mechanism;
configuration loading must not trigger import-time I/O, connection creation or hardware access. Keep pure policy
importable with deterministic test inputs.

Python annotations are not runtime validation. Check untrusted input at its admission boundary and narrow it before
policy execution; avoid using `Any`, unchecked casts or blanket exception handling to hide an invalid contract.
Run the package's declared type/lint checks when present. If none are configured, report that gap rather than claiming
type enforcement or adding a new checker merely to satisfy prose.

## Compatibility and migrations

Remove or migrate a public interface only within an explicit compatibility decision. Account for exports, aliases,
wire fields, generated clients, package consumers and unknown external users; no local callers does not prove no users.
Preserve supported behavior and safety coverage until the replacement and affected consumers are accounted for.
Record proposed/current/deprecated status, relevant evidence, rollback and unresolved external compatibility. This rule
does not authorize a release, production traffic, dependency upgrade or removal merely because code is old.

## I/O, errors, lifecycle and safety

Validate at trust boundaries; preserve authorization, schemas, limits, error/status semantics and compatibility paths.
Do not turn failures into apparently successful fallbacks. Retries need bounds, idempotency reasoning and observable
outcomes. A refactor preserves deadlines, ordering, identity checks and branch priority where those affect behavior.

External I/O needs appropriate timeouts, size limits and endpoint admission. Moving blocking work into an adapter does
not make it nonblocking. Owned tasks/resources have an owner, bounded shutdown and cancellation semantics; partial
startup must clean up acquired resources, and one failing closer must not hide other cleanup or its own failure.

Inspect illustrative algorithms before reuse: an async example may discard failed results, a context manager's exit
method may not run after failed entry, and a background task may outlive its caller. Tutorial scripts, `setup.py`
examples, permissive auth/CORS snippets and dependency-install commands are reference material, not approved setup.

Keep safety authority where the actual system declares it. Tests use fakes/fixtures/isolated software endpoints;
hardware access, movement, firing, recovery, live transport writes and deployment require separately scoped authority.
A queued action, software ACK, build, simulation or log line is not physical completion.

When firmware is actually in scope, inspect its selected board/build environment, pin/electrical profile, calibration,
transport and safe-state authority before reusing an example. Run only the explicitly selected native environment;
firmware is not a Python package by default. Software fixtures, a size/build result or a flashing/hash check cannot
prove polarity, timing, motion or firing safety. Preserve project-specific human approval and non-actuating defaults.

## SRP, branching and extraction

There is no universal function/file line-count cap. Size, nesting and duplication are investigation signals. Extract a
cohesive named responsibility with explicit inputs/outputs when it improves caller leverage, locality or testability.
Keep needed error handling and validation; avoid move-only layers, forwarding wrappers and speculative extension points.

Use guards, tables, loops or polymorphism according to the actual decision. Preserve ordering where it is meaningful.
In React, clarify state ownership and pure decisions before extracting effects; retain cancellation, stale-result
guards, dependencies, loading/error behavior and accessibility. State-only work is not an automatic visual redesign.

## Verification is claim-specific

| Change | Required kind of evidence |
| --- | --- |
| Guidance/directory scaffold | Metadata parsing, local references, inventory/provenance/licenses and complete-file whitespace/diff review |
| New or repaired behavior | Meaningful failing behavioral assertion, minimal change, passing focused checks and actual package gates |
| Preserved behavior | Characterization before extraction and retained boundary/integration coverage |
| Shared/native contract | Every producer/consumer and native environment, seam regressions, compatibility limits and separate review |
| Deployment or physical behavior | Separately authorized environment-specific evidence; not inferred from software checks |

Use the actual owning package's test, typecheck, lint and build commands declared in its README/native configuration.
During iteration run focused checks; before completion run the applicable package/repository gates unless execution
is explicitly excluded, and report every observed failure. If a gate is absent, record that gap rather than inventing
a passing `check` command or bootstrapping applications merely to verify prose. Missing imports/broken fixtures
are not a behavioral bug reproduction. Keep low-level malformed-input, cancellation and cleanup tests when broader
interface coverage does not replace their failure cases. Generated files are changed through their inspected source.

Tests use Arrange–Act–Assert and protect observable output, state, errors and relevant side effects. Narrow fixtures
control time/random/I/O without global successful fallbacks or shared-state pollution. Unit tests cover pure decisions;
adapter/integration tests cover actual I/O semantics; public API/CLI/UI/package tests protect consumers. A fake validates
the policy's use of a contract, not the production adapter itself. Extension tests retain existing variants and check
the new variant's success/error/lifecycle behavior. Do not trade malformed-input or shutdown coverage for fewer tests.

## Curated source adaptations

Applicable imported and authored skills retain substantive procedures, worked guidance and provenance/license records;
this section is not a substitute that reduces them to names or links. The catalog (look up `.agents/README.md` in the consuming repository; its current project guidance remains authoritative) routes by actual task
and native package, not by source author. Preserve applicable design, testing, API, architecture, naming and review
procedures during imports or template updates; a source archive or summary is not their replacement. These neutral
constraints govern all source families' generic examples; package-specific adaptations belong in the adopted target,
not in an unrelated wrapper.

- **Design and architecture:** preserve domain vocabulary, public APIs and state/safety ownership. A useful seam does
  not require two adapters, an ABC, a repository interface or a rich domain model. Compare alternatives proportionately.
- **Python structure and testing:** keep the actual supported Python versions and native environment; do not mechanically
  add `__all__`, `setup.py`, tutorial directories or coverage thresholds. Reuse real fixtures and protect failure behavior.
- **Security:** identify the untrusted writer, asset and abuse case before selecting controls. Browser headers, cookies,
  CSP, CORS and HTTPS apply to relevant exposures, not all native/local transports. Preserve admission/auth/error contracts;
  no automatic audit fixes, dependency upgrades, history rewrites, external integrations or secret disclosure.
- **Observability:** begin with a concrete diagnostic gap and existing signals. Keep bounded dimensions, correlation and
  redaction; JSON, OpenTelemetry, vendors, dashboards and live traffic are optional scoped choices, not universal gates.
- **React and design:** match installed React/framework/runtime support. Next.js/RSC/server-action or newer React APIs
  are conditional examples, not migration requirements. Preserve the target's design brief and accessibility; never
  fabricate data or remove loading/error behavior to improve a screenshot.
- **Resource/async examples:** review result accounting, partial acquisition, task lifetime, cancellation and independent
  cleanup. Do not execute bundled scripts, start services or install dependencies simply because an example mentions them.
- **Agent writing:** use precise triggers, progressive references and observable completion criteria. Retain real scope,
  safety, authority, lifecycle and rollback constraints. Metadata and file presence do not prove discovery or adherence.
- **Imported tooling:** resource closure and source/local hashes are static checks, not source authenticity or runtime proof.
  Host plugin hooks, MCP connections, credentials and personal configurations are not part of a copied skill.

When Rust or firmware is selected, reach its native references and available skills through the project catalog.
Do not import a source repository's SDK, transport, hardware or release assumptions as universal language rules.

## Review and reporting

Review the whole changed slice, including callers, tests, fixtures, native configuration and current docs:

- **Correctness/contracts:** input bounds, state/identity/order/deadline behavior, compatibility and available consumers.
- **Design/naming:** responsibility, dependency direction, public surface, unnecessary abstraction and domain vocabulary.
- **Trust/lifecycle:** auth/admission, sensitive data, error mapping, retries/idempotency, cancellation and partial cleanup.
- **Tests/performance:** assertions that would catch the defect, deterministic isolation, relevant failure cases, actual
  native gate results, and measured resource/performance concerns instead of speculative caching or parallelism.
- **Change impact:** migration/removal plan, generated-source ownership, README/spec synchronization and safe rollback.

For substantial contract, concurrency, safety or routing changes, use an independent reviewer. Findings name severity,
location, failure condition, evidence and the smallest correction; unsupported concerns remain questions. Report changed
boundaries, observed checks, omissions, compatibility risk and rollback. Distinguish blocking failures from optional style
suggestions; formatter choices and numeric PR/file-size heuristics are not semantic correctness gates. Static, software,
deployed and physical evidence remain distinct. The task brief (shared skill `common:writing-plans`; select the `common` bundle when that task boundary is in scope) makes ownership and allowed
side effects explicit.

## Shared methodology references

For a meaningful development/verification workflow decision, read the [development loop](development.md): SDD, TDD,
selective DDD and source-first evidence. For responsibility/pattern/reuse decisions, read the
[worked architecture example](architecture.md). These are shared references, not project-owned copied manuals.
Actual current product contracts and decisions stay in the consuming project's specs and ADRs.
