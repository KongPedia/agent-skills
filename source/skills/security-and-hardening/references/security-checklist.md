# Security Checklist

Quick reference for affected security boundaries. Use alongside [security-and-hardening](../SKILL.md); mark web-only sections not applicable for native transports. Existing auth, schemas, response mapping, configuration and current task authority take precedence over illustrative defaults.

## Table of Contents

- [Threat Modeling (Start Here)](#threat-modeling-start-here)
- [Pre-Commit Checks](#pre-commit-checks)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Input Validation](#input-validation)
- [Security Headers](#security-headers)
- [CORS Configuration](#cors-configuration)
- [Data Protection](#data-protection)
- [Dependency Security](#dependency-security)
- [AI / LLM Security](#ai--llm-security)
- [Error Handling](#error-handling)
- [OWASP Top 10 Quick Reference](#owasp-top-10-quick-reference)
- [OWASP Top 10 for LLMs Quick Reference](#owasp-top-10-for-llms-quick-reference)

## Threat Modeling (Start Here)

Before reaching for controls, spend five minutes thinking like an attacker:

- [ ] Trust boundaries mapped (requests, uploads, webhooks, third-party APIs, LLM output, and local values written by processes you don't control)
- [ ] Assets named (credentials, PII, payment data, admin actions, money movement)
- [ ] STRIDE run per boundary (Spoofing, Tampering, Repudiation, Info disclosure, DoS, Elevation)
- [ ] Abuse cases written next to use cases ("how would I misuse this?")

## Pre-Commit Checks

Only when a commit is separately authorized; these checks do not authorize one. Preserve intentional tracked templates and fixtures when reviewing ignore patterns.

- [ ] No secrets in code (`git diff --cached | grep -i "password\|secret\|api_key\|token"`)
- [ ] `.gitignore` covers: `.env`, `.env.local`, `*.pem`, `*.key`
- [ ] `.env.example` uses placeholder values (not real secrets)

## Authentication

Apply the items matching the current auth mechanism; do not introduce passwords, cookies, JWTs, MFA or new dependencies merely to complete the list.

- [ ] Passwords hashed with bcrypt (≥12 rounds), scrypt, or argon2
- [ ] If cookie sessions exist, flags and CSRF handling match deployment and authentication requirements
- [ ] Session expiration configured (reasonable max-age)
- [ ] Applicable login limits follow current policy and abuse-risk evidence, not a fixed example threshold
- [ ] If password reset exists, tokens have the approved bounded lifetime and single-use behavior
- [ ] Account lockout after repeated failures (optional, with notification)
- [ ] MFA supported for sensitive operations (optional but recommended)

## Authorization

- [ ] Every protected endpoint checks authentication
- [ ] Every resource access checks ownership/role (prevents IDOR)
- [ ] Admin endpoints require admin role verification
- [ ] API keys scoped to minimum necessary permissions
- [ ] JWT tokens validated (signature, expiration, issuer)

## Input Validation

- [ ] All user input validated at system boundaries (API routes, form handlers)
- [ ] Validation uses allowlists (not denylists)
- [ ] String lengths constrained (min/max)
- [ ] Numeric ranges validated
- [ ] Email, URL, and date formats validated with proper libraries
- [ ] File uploads: type restricted, size limited, content verified
- [ ] SQL queries parameterized (no string concatenation)
- [ ] HTML output encoded (use framework auto-escaping)
- [ ] URLs validated before redirect (prevent open redirect)
- [ ] Server fetches follow explicit endpoint admission; public user-directed URLs cannot reach disallowed internal targets; approved local integrations retain their existing policy
- [ ] Destructive path operations (delete/move/overwrite): symlinks resolved, allowlisted root, minimum depth, ownership evidence read before the call

### Destructive Path Operations

Containment for a target named by data. Resolve first, then decide — and treat the
result as a candidate, not as authorization:

```typescript
import { realpath, readFile } from 'node:fs/promises';
import { resolve, relative, isAbsolute, join, sep } from 'node:path';

const ALLOWED_ROOTS = ['/var/lib/myapp/sessions']; // an allowlist, not a pattern
const MIN_DEPTH = 1;                               // so a root is never the target

async function resolveDeletable(candidate: string, expectedOwner: string) {
  const target = await realpath(resolve(candidate)); // symlinks resolved BEFORE the check
  const inRoot = ALLOWED_ROOTS.some((root) => {
    const rel = relative(root, target);
    // `rel === '..'` / `'../'` only — a plain `startsWith('..')` would also
    // reject a legitimate child named `..cache`.
    if (rel === '' || rel === '..' || rel.startsWith(`..${sep}`) || isAbsolute(rel)) return false;
    return rel.split(sep).length >= MIN_DEPTH;
  });
  if (!inRoot) throw new Error(`refusing: outside allowed roots (${target})`);

  const owner = await readFile(join(target, '.owner'), 'utf8').catch(() => null);
  if (owner?.trim() !== expectedOwner) throw new Error(`refusing: unproven owner (${target})`);
  return target;
}
```

What this does not do, and must be said where the snippet is copied from:

- **The marker is self-attestation.** Anything that can write inside the root can write
  `.owner`. `expectedOwner` has to come from authenticated state, and the marker needs
  integrity protection (restrictive ownership, or a MAC) before it is authorization
  rather than a consistency check against a misderived target.
- **Returning a path leaves a check/use race.** Where an untrusted process can swap an
  ancestor between the check and the call, operate on a descriptor with no-follow,
  beneath-the-root semantics, or guarantee the hierarchy is immutable for the duration.

## Security Headers

HTTP/browser examples only: preserve the actual embedding/media/robot-control requirements. Do not copy camera/microphone/geolocation bans or CSP origins into an operator UI without contract review.

```
Content-Security-Policy: default-src 'self'; script-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0  (disabled, rely on CSP)
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## CORS Configuration

```typescript
// Restrictive (recommended)
cors({
  origin: ['https://yourdomain.com', 'https://app.yourdomain.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
})

// Broad public origins require an explicit exposure decision, not a copied default.
// Never combine wildcard origins with credentialed requests.
cors({ origin: '*' })  // Example of broad origin exposure, not a recommended default
```

## Data Protection

- [ ] Sensitive fields excluded from API responses (`passwordHash`, `resetToken`, etc.)
- [ ] Sensitive data not logged (passwords, tokens, full CC numbers)
- [ ] PII encrypted at rest (if required by regulation)
- [ ] HTTP transport security matches actual exposure; native/approved local transports keep their established security and endpoint-admission contract
- [ ] Database backups encrypted
- [ ] Personal data is classified, collected against a stated purpose, and minimized
- [ ] Personal data has a retention limit and a working deletion path (incl. backups, caches, indexes)
- [ ] Export/delete (data-subject) requests are supported where required; third-party sharing has consent and a data-processing agreement

## Dependency Security

First locate the **installation boundary**. If the package is matched by a parent `workspaces` declaration, use that workspace root; otherwise use the nearest project root that owns both its manifest and dependency graph. At that boundary, corroborate `packageManager` (when present), the lockfile, and CI commands. Stop if they disagree or competing manager lockfiles exist there. A nested project is independent only when it is outside the parent workspace; independent subprojects may legitimately use different managers.

| Manager/version signal | Frozen/immutable CI install | Known-advisory audit |
|---|---|---|
| npm (`package-lock.json` or `npm-shrinkwrap.json`) | `npm ci` | `npm audit` |
| pnpm | `pnpm install --frozen-lockfile` | `pnpm audit` |
| Yarn 2+ | `yarn install --immutable` | `yarn npm audit -A -R` |
| Yarn 1 | `yarn install --frozen-lockfile` | `yarn audit` |

For an unlisted manager or version, consult its official documentation; do not substitute another manager's commands or newer defaults.

### Install-Script Gate

Review scripts before their first authorized execution. This checklist does not authorize
setup, installs, commits, manager upgrades or CI policy changes. Use the existing locked
environment and repository commands; guidance-only reviews remain static.

1. Inspect the pinned manager's documented script policy and the exact package/script source.
2. Identify any missing fail-closed behavior and the narrowest required exception.
3. Report a needed policy repair if outside task scope. Within authorized dependency work,
   use the pinned client's supported policy rather than blanket approval.
4. Validate an authorized policy change with the owning frozen/immutable-install gate,
   without silently changing lockfiles or adding another package manager.

Manager defaults vary by version. Consult the current official documentation for the
project's pinned client before proposing commands: [npm](https://docs.npmjs.com/cli/),
[pnpm](https://pnpm.io/settings), [Yarn](https://yarnpkg.com/features/security).
The table above identifies ecosystems; it does not replace the owning package's gates.

**Supply-chain hygiene** (advisory audits do not catch newly malicious packages):
- [ ] Exactly one authoritative lockfile per project/workspace root is committed and CI never rewrites it
- [ ] Critical/high findings are triaged for reachability; deferrals have a reason and review date
- [ ] Forced audit remediation (`npm audit fix --force` or equivalent) is never automatic; remediation diffs and changelogs are reviewed
- [ ] Registry signatures/provenance are verified where the manager supports it
- [ ] Dependency script risks are reviewed before authorized execution; any missing policy is reported, not bypassed or silently replaced
- [ ] New dependencies are reviewed for ownership, maintenance, release age, provenance, transitive graph, and typosquatting

## AI / LLM Security

For any feature that calls an LLM (chatbots, summarizers, agents, RAG):

- [ ] Model output treated as untrusted — never into `eval`/SQL/shell/`innerHTML`/file paths
- [ ] Prompt injection assumed; permissions enforced in code, not in the system prompt
- [ ] Secrets, cross-tenant data, and full system prompts kept out of the context window
- [ ] Tool/agent permissions and existing destructive-action authorization boundary are enforced; no repeated confirmation is imposed on already authorized safe local work
- [ ] Token, rate, and recursion/loop limits set (bound consumption)

## Error Handling

Illustrative new HTTP response only; existing routes preserve status/detail/envelope while excluding secrets and internals.

```typescript
// Production: generic error, no internals
res.status(500).json({
  error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' }
});

// NEVER in production:
res.status(500).json({
  error: err.message,
  stack: err.stack,         // Exposes internals
  query: err.sql,           // Exposes database details
});
```

## OWASP Top 10 Quick Reference

| # | Vulnerability | Prevention |
|---|---|---|
| 1 | Broken Access Control | Auth checks on every endpoint, ownership verification |
| 2 | Cryptographic Failures | HTTPS, strong hashing, no secrets in code |
| 3 | Injection | Parameterized queries, input validation |
| 4 | Insecure Design | Threat modeling, spec-driven development |
| 5 | Security Misconfiguration | Security headers, minimal permissions, audit deps |
| 6 | Vulnerable Components | The ecosystem's dependency audit (`npm audit`, `pip-audit`, ...), keep deps updated, minimal deps |
| 7 | Auth Failures | Strong passwords, rate limiting, session management |
| 8 | Data Integrity Failures | Verify updates/dependencies, signed artifacts |
| 9 | Logging Failures | Log security events, don't log secrets |
| 10 | SSRF | Validate/allowlist URLs, restrict outbound requests |

## OWASP Top 10 for LLMs Quick Reference

For apps with LLM features. See the [OWASP GenAI Security Project](https://genai.owasp.org/llm-top-10/).

| ID | Risk | Prevention |
|---|---|---|
| LLM01 | Prompt Injection | Don't trust the system prompt as a boundary; enforce permissions in code |
| LLM02 | Sensitive Information Disclosure | Keep secrets/PII out of prompts; filter outputs |
| LLM03 | Supply Chain | Vet models, datasets, and plugins like any dependency |
| LLM04 | Data and Model Poisoning | Use trusted model sources, verify integrity; vet fine-tuning and RAG data |
| LLM05 | Improper Output Handling | Treat model output as untrusted; validate, parameterize, encode |
| LLM06 | Excessive Agency | Scope tool permissions; confirm destructive actions |
| LLM07 | System Prompt Leakage | Assume the system prompt can leak; put no secrets in it |
| LLM08 | Vector and Embedding Weaknesses | Partition RAG embeddings per tenant; validate documents before indexing |
| LLM09 | Misinformation | Ground answers with citations; validate critical claims; keep a human in the loop |
| LLM10 | Unbounded Consumption | Cap tokens, request rate, and loop/recursion depth |
