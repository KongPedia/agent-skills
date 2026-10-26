---
name: litestar-backend
description: Develop or review Litestar routes, DI/lifespan ownership, typed HTTP contracts, guards and API tests.
---

# Litestar backend

Inspect the owning package's manifest, lock, app factory and HTTP tests first. Match its installed Litestar version,
validation models and existing collaborators. In a monorepo, use that backend's environment. The starter targets
Litestar 2.25; `/main/` documentation may describe an unreleased major version. This is original scoped development
guidance, not a vendored upstream skill or a mandate to adopt the surrounding Litestar ecosystem.

## Procedure

1. **Contract:** identify consumers, accepted inputs, status/payload/error semantics and authorization owner.
   Write a success test and the changed rejection/failure test before implementing behavior. Reuse the common
   API design procedure (shared skill `api-contracts:api-design-principles`; select the `api-contracts` bundle when that task boundary is in scope) instead of inventing a second wire contract here.
2. **Composition:** register a small route directly when sufficient. Introduce a `Router` or `Controller` for shared
   prefixes, configuration or feature ownership; inspect inherited guards/dependencies on every affected route.
   Keep transport validation/mapping at the handler and independently changing policy in a concrete collaborator.
   Neither a database, repository abstraction, plugin nor a fixed domain folder hierarchy is a prerequisite.
3. **Validation:** declare request sources and typed bodies explicitly using APIs supported by the installed version.
   Keep runtime-inspected annotation types resolvable at app construction; moving them behind `TYPE_CHECKING` can break
   signature resolution. Separate writable inputs from public outputs. If DTOs/ORMs are present, allow only intended
   fields and test overposting and sensitive-field exclusion; do not add a new DTO/model library for a health endpoint.
4. **Dependency scope:** use the existing DI mechanism. Native `Provide` keys and `NamedDependency[T]` parameter names
   must agree on Litestar 2.25; implicit name-only injection is deprecated. Declare dependencies at the narrowest
   meaningful route/controller/router/app layer. Declaration scope is not resource lifetime: a reusable app-level
   declaration can still produce request-specific values. Keep `use_cache` off for identity, tenant or request-owned
   state; it memoizes across calls rather than varying by request arguments. Test isolation between requests.
5. **Lifecycle:** acquire shared clients in the app's lifespan owner, request resources in generator dependencies
   with `try/finally`, and deterministic policy without I/O. Cover partial acquisition, handler failure and cleanup.
   Generator cleanup occurs before an HTTP response is sent: a stream/background task must not borrow a resource that
   its request dependency already released. Give such work an explicit owner and test its actual lifetime.
6. **Concurrency:** inspect I/O calls. Use async clients for async handlers; `async def` alone does not unblock a sync
   driver. Set `sync_to_thread=True` for a blocking sync handler/provider, or explicitly `False` for short nonblocking
   work such as the starter health response. Thread offload is not CPU parallelism or cancellation of a worker/remote
   side effect. Preserve deadlines, bounded work and cleanup with the existing async/resource procedures.
7. **Admission and errors:** authenticate through the existing middleware/backend and authorize through the established
   guard/policy owner. A public-route authentication bypass does not automatically bypass inherited guards. Test actual
   allowed and denied requests, including tenant/resource ownership where applicable. Translate domain failures at the
   HTTP exception boundary; keep debug details/secrets out of responses and retain the established error schema.
8. **Evidence:** enter `TestClient` or `AsyncTestClient` as a context manager so lifespan runs and exits. Use the async
   client when tests share async resources and must use the same event loop. Build a fresh app with test providers at
   the real declaration scope; Litestar does not have FastAPI's `app.dependency_overrides` registry. Keep the real guard
   and replace its external identity/I/O collaborator, not all authorization with success. Run the package's declared
   HTTP tests, type/lint checks and build; use isolated software clients/fakes, not production services or hardware.

## Completion

Report changed route and inherited configuration, preserved authorization/error contracts, success/rejection/lifecycle
coverage and exact native check results or omissions. A passing health response proves neither readiness nor production
security, load behavior, interoperability or physical action. This skill does not authorize dependency upgrades,
external services, deployment, publication or device access.

## Primary references

Read only the branch needed for the installed release:

- [Routing and layered configuration](https://docs.litestar.dev/2/usage/routing/overview.html)
- [Handlers, synchronous work and threading](https://docs.litestar.dev/2/usage/routing/handlers.html)
- [DI markers, caching, overrides and cleanup](https://docs.litestar.dev/2/usage/dependency-injection.html)
- [Application state and lifespan](https://docs.litestar.dev/2/usage/applications.html)
- [DTO input/output boundaries](https://docs.litestar.dev/2/usage/dto/0-basic-use.html)
- [Guards](https://docs.litestar.dev/2/usage/security/guards.html) and
  [exception mapping](https://docs.litestar.dev/2/usage/exceptions.html)
- [Test clients, lifecycle and dependency substitution](https://docs.litestar.dev/2/usage/testing.html)

The [first-party Litestar skills v0.6.0][upstream-skills]
are an optional deeper resource for an actually selected ecosystem package. Their broad stack/layout preferences are not
template requirements; host plugins, hooks and sibling skill collections are not installed or copied here.

[upstream-skills]: https://github.com/litestar-org/litestar-skills/tree/150bdbebadf79022bd0440e6f3ddcfde22b74f4e
