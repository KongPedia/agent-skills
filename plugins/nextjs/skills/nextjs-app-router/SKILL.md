---
name: nextjs-app-router
description: Implement or review a Next.js App Router package's server/client boundaries, routes, mutations and rendering behavior. Not for React Vite, NestJS or Pages Router migrations.
---

# Next.js App Router

Start with the owning package's manifest, lock, `src/app` routes and scoped instructions. Read relevant installed-version
docs from that package's `node_modules/next/dist/docs/` when available, not a hoisted path guessed from the monorepo root.
Next.js 16.2+ bundles documentation; 16.3+ supports managed instructions. Confirm behavior for the actual installed version
using the [official agent guide](https://nextjs.org/docs/app/guides/ai-agents).

## Procedure

1. Trace the changed route, layouts, data reads/mutations and consumers. Define what is server-authoritative and what is
   browser interaction. Test the observable behavior and failure boundary rather than a framework-shaped folder tree.
2. Keep server-only credentials and I/O out of client imports and serialized props. Introduce a client boundary only
   for required interaction/browser APIs. Reuse the applicable React/composition/design skills without applying Next
   server APIs to an unrelated React SPA.
3. Treat Route Handlers and server mutations as trust boundaries: validate input, authenticate/authorize each operation,
   and preserve error/status semantics. A server file or hidden button is not authorization.
4. Inspect caching/revalidation, async request APIs and runtime support in the installed-version docs before changing
   them. Preserve freshness and per-user isolation; do not enable experimental caching or force a migration for a skill.
5. Cover loading, error, empty and keyboard/accessibility states where UI changes. Run the package's declared checks
   and production build; verify changed routes at the relevant HTTP/browser layer when that behavior is in scope.
   Typecheck/build alone do not prove hydration, navigation or authorization.

## Managed instructions and completion

When `next dev` manages an AGENTS block, preserve the project's rules outside its markers and review the resulting diff.
In a monorepo, distinguish the Next app's scoped AGENTS from the repository contract. Do not enable optional feedback,
MCP tools, canary upgrades, telemetry or external submissions merely because upstream guidance mentions them.

Report the package/version, changed boundaries, actual checks and omissions. One full-stack Next app is one component;
it does not require creating a separate Nest backend. Product deployment and dependency upgrades remain separate scope.
