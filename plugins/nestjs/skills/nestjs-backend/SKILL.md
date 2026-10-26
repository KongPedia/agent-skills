---
name: nestjs-backend
description: Implement or review a NestJS backend's modules, providers, HTTP boundaries, lifecycle and tests. Use only for NestJS packages, not generic TypeScript or React projects.
---

# NestJS backend

Read the owning package's manifest, lock, TypeScript/module settings, bootstrap and feature modules. Match the installed
Nest major and HTTP adapter; framework examples are not an instruction to upgrade. Consult the
[official migration guide](https://docs.nestjs.com/migration-guide) when version-specific behavior matters.

## Procedure

1. Trace controller → provider → actual I/O and each affected caller. Specify the observable request/result/error and
   authorization boundary; write the relevant regression before changing behavior.
2. Let controllers translate transport input/output. Providers own cohesive operations; modules own wiring and explicit
   imports/exports. Export the needed provider, not an entire implementation tree. Avoid circular dependencies and
   global modules used only to avoid understanding ownership.
3. Validate untrusted input through the package's existing pipeline. Preserve guards, pipes, filters and interceptor
   ordering where it changes behavior. DTO/type declarations alone do not establish runtime validation or authorization.
4. Check async cleanup, shutdown hooks and owned clients. A singleton provider is not a per-request state store.
   Do not add a database/ORM, generic repository, CQRS or microservice transport without a concrete requirement.
5. Use the existing test runner with Nest's testing utilities where DI wiring matters; override an actual external
   provider at that boundary and close created applications. Unit tests of a controller method do not prove HTTP
   routing, validation or guards. See [official testing](https://docs.nestjs.com/fundamentals/testing).
6. Run the owning package's declared typecheck, tests and build. For ESM/NodeNext packages verify runtime imports and
   emitted module resolution, not just editor types; do not paste CommonJS-era configuration into a different major.

## Completion

Report the affected route/provider/module contracts, observed package checks and gaps. Keep test I/O isolated from
production and physical devices. Do not infer product readiness from a starter health test. Installation, upgrades,
external integrations, publishing and deployment require their own authorized scope.
