---
name: fastapi-backend
description: Implement or review an existing FastAPI backend's request contracts, dependency lifetimes, async boundaries and API tests. Not for Python import libraries or choosing a framework.
---

# FastAPI backend

Use the owning package's README, `pyproject.toml`, lock and installed FastAPI/Pydantic versions. In a monorepo,
work from that backend package, not a different root environment. This is original project guidance, not vendored
FastAPI documentation; use the [official testing guide](https://fastapi.tiangolo.com/tutorial/testing/) for current APIs.

For version-sensitive behavior, inspect the matching installed package's bundled `fastapi/.agents/skills/fastapi/`
when available; the [official tutorial](https://fastapi.tiangolo.com/tutorial/#ai-agent-skills) explains this resource.
The starter's [0.162.0 skill and references](https://github.com/fastapi/fastapi/tree/7a0a3f0b286c6c865cf4398ea0e957a87b8bffa4/fastapi/.agents/skills/fastapi)
are first-party development guidance. This local procedure deliberately does not bundle their broader Asyncer,
SQLModel, CLI or telemetry preferences. Reuse the project's selected tools and check examples for blocking I/O;
an upstream preference is not permission to add a dependency or replace an existing architecture.

## Procedure

1. Inspect the changed route and its callers: request/response schemas, status codes, auth, error mapping and existing tests.
   Define an observable success case and the relevant rejection/failure case before changing behavior.
2. Keep HTTP validation/translation at the route. Put actual policy in a named function or concrete collaborator when it
   changes independently; do not introduce repository interfaces, a database or domain layers for an empty example.
   Declare the public response schema and test that internal or sensitive fields cannot escape through serialization.
3. Check every I/O call. `async def` does not make a blocking client nonblocking. Preserve deadlines, cancellation and
   resource ownership; use existing dependency injection rather than hidden clients created inside business policy.
4. When startup/shutdown changes, use the package's lifespan contract and test acquisition and cleanup. TestClient must
   enter its context when the test depends on lifespan execution; see [lifespan tests](https://fastapi.tiangolo.com/advanced/testing-events/).
   Reset test dependency overrides so one test cannot alter later requests.
   Choose a `yield` dependency's supported scope according to whether its resource must survive response streaming;
   test cleanup timing on success and failure. Background work must not borrow an already released request resource.
5. Run the owning package's declared tests/checks. API tests assert status and payload/error semantics, not merely that
   the app imports. Use isolated software clients and fakes; do not contact production databases, brokers or hardware.

## Completion

Report changed routes/contracts, behavior protected by tests, exact package checks and omitted checks. A health endpoint
is a starter smoke check, not readiness, security, production deployment or product acceptance. Preserve auth and response
compatibility during refactors. This skill does not authorize dependency installation/upgrades, publishing or deployment.
