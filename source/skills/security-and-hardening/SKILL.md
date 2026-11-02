---
name: security-and-hardening
description: Review or implement security-relevant trust boundaries, authentication, authorization, sensitive data handling, dependency-audit findings or untrusted-input defenses. Use when those controls are in task scope or a concrete security risk is identified; not every feature or routine prose edit.
---

# Security and Hardening

## Overview

Security-first development practices, with web-specific controls applied only to web surfaces. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security isn't a phase — it's a constraint on every line of code that touches user data, authentication, or external systems.

> Selectively vendored and adapted; [project adaptations](../../references/engineering.md#curated-source-adaptations) and owning contracts govern scope, environments and safety. See [provenance](../../skill-sources.json).

## When to Use

- Reviewing or changing a concrete untrusted-input boundary
- Implementing authentication or authorization
- Storing or transmitting sensitive data
- Integrating with external APIs or services
- Adding file uploads, webhooks, or callbacks
- Handling payment or PII data

## Process: Threat Model First

Controls bolted on without a threat model are guesses. Before hardening, map the affected boundaries proportionately before choosing controls:

1. **Map the trust boundaries.** Where does untrusted data cross into your system? HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, and **LLM output** — plus the local values that look internal because the OS handed them to you: another process's command line or environment, filenames on a shared volume, a path in a job payload. Trust follows who *wrote* a value, not which channel delivered it. Every boundary is attack surface.
2. **Name the assets.** What's worth stealing or breaking? Credentials, PII, payment data, admin actions, money movement.
3. **Run STRIDE over each boundary** — a quick lens, not a ceremony:

| Threat | Ask | Typical mitigation |
|---|---|---|
| **S**poofing | Can someone impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, HTTPS |
| **R**epudiation | Can an action be denied later? | Audit logging of security events |
| **I**nformation disclosure | Can data leak? | Encryption, field allowlists, generic errors |
| **D**enial of service | Can it be overwhelmed? | Rate limiting, input size caps, timeouts |
| **E**levation of privilege | Can a user gain rights they shouldn't? | Authorization checks, least privilege |

4. **Write abuse cases next to use cases.** For each feature, ask "how would I misuse this?" — then make that your first test.

If you can't name the trust boundaries for a feature, you're not ready to secure it. This is OWASP **A04: Insecure Design** — most breaches begin in design, not code.

## Control applicability and authority

### Preserve protections at the affected boundary

- Validate external input with the existing schema/codec; parameterize database queries and encode browser output where those surfaces exist.
- Keep credentials out of source and telemetry; use the existing secrets/configuration owner.
- For an affected password store, use an approved password hash. For an affected browser session, review cookie flags, CSRF and expiration against its current authentication architecture.
- Review HTTPS, headers and CORS for the HTTP/browser exposure actually present. These are not requirements to replace existing non-HTTP or offline transport contracts.
- Use existing locked audit/check commands when application/dependency validation is authorized; guidance-only work stays static.

### Keep changes inside the requested authority

For requested security updates, complete the authorized local work without repeated confirmation.
Changes to authentication, sensitive-data collection, external integrations, CORS, uploads,
rate limits or roles must fit the task and owning contracts. If a newly identified change
would expand scope, report the risk and needed handoff instead of silently redesigning it.
Existing schemas, response/status mapping, authentication and transport contracts remain
authoritative unless their change is explicitly included.

### Avoid unsafe shortcuts

- Never commit secrets or log passwords, tokens or full sensitive records.
- Client-side validation is not a security boundary; enforce authorization in the owning service.
- Preserve existing security controls; report a needed migration rather than weakening them for convenience.
- Never feed untrusted data to `eval`, SQL, shell execution or raw HTML without the corresponding safe boundary.
- For browser-session design in scope, prefer storage inaccessible to script when compatible with the architecture; do not silently replace an existing token/session flow.
- Preserve public error contracts while excluding stack traces, secrets and internal query details.

## Hardening Controls

The rules below are the workflow; a concrete implementation of each lives in [references/hardening-patterns.md](references/hardening-patterns.md). Open the section you need when you reach that code, not before.

### Injection, XSS, and access control

- Parameterize every query. Never build SQL, NoSQL, or shell commands from input strings.
- Encode output through the framework's auto-escaping. If raw HTML is unavoidable, sanitize with an allowlist sanitizer first.
- Check **authorization** on every request, not just authentication: the authenticated user must own, or be permitted on, the specific resource (A01, IDOR).

Patterns: [Injection](references/hardening-patterns.md#injection), [XSS](references/hardening-patterns.md#cross-site-scripting-xss), [Access control](references/hardening-patterns.md#broken-access-control).

### Authentication and sessions

- Where password storage is in scope, use the owning implementation's approved bcrypt/scrypt/argon2 policy; do not introduce a dependency or auth migration solely for this example. Session secrets use the existing secrets owner, never source literals.
- For browser cookie sessions, review `httpOnly`, `secure`, `sameSite` and bounded lifetime together with CSRF and deployment requirements. Cookie flags alone are not a universal CSRF defense; native/token transports do not become cookie sessions.

Pattern: [Authentication](references/hardening-patterns.md#broken-authentication).

### Headers, CORS, and responses

- For HTTP/browser responses in scope, review existing security headers and CSP against the actual embedding, media and connection requirements; preserve approved origins and feature permissions.
- CORS restricted to an explicit origin list from configuration. Never `*` with credentials.
- Exclude sensitive fields (`passwordHash`, reset tokens) from responses. Preserve established error status/detail/envelopes while keeping secrets, stacks and internal queries out of public output and sensitive data out of logs.

Patterns: [Misconfiguration](references/hardening-patterns.md#security-misconfiguration), [Sensitive data exposure](references/hardening-patterns.md#sensitive-data-exposure).

### Input validation and uploads

- Validate at the boundary with the existing schema: allowlisted shape, lengths, enums and formats. Preserve current rejection status/detail and wire keys; downstream code uses the parsed, typed value. A generic 422 example does not authorize a new response contract.
- Uploads: allowlist MIME types, cap size, verify content (magic bytes) when it matters. The extension proves nothing.

Patterns: [Schema validation](references/hardening-patterns.md#schema-validation-at-boundaries), [File upload](references/hardening-patterns.md#file-upload-safety).

### Server-side fetches (SSRF)

Any URL the user influences — webhooks, import-from-URL, image proxies, link previews — can be aimed at internal services. For public user-directed fetches, allowlist scheme and host, resolve **all** DNS records and reject disallowed private or reserved addresses (loopback, link-local `169.254.169.254`, private, unique-local, for IPv4 and IPv6), and control redirects. Purpose-built local robot/service integrations need their existing explicit endpoint admission, not a blanket ban on private addresses. That check still has a DNS-rebinding TOCTOU gap: for high-risk surfaces, pin the resolved IP or put a filtering agent in front.

Pattern: [SSRF](references/hardening-patterns.md#server-side-request-forgery-ssrf).

### Destructive operations on derived paths

A delete, move, or overwrite is only as safe as the value naming its target, and trust follows who *wrote* that value, not which channel delivered it: another process's command line is as attacker-controlled as a form field. A shape check proves well-formedness, not authorization. Before the call, require all three: the resolved target (symlinks resolved) sits under an **allowlisted root**; it is at least one level **below** that root; and it carries **ownership evidence read before the operation**. On refusal, log the rejected target and stop; never fall back to a broader default path.

Why the check is weaker than it reads (marker self-attestation, check/use races): [Destructive paths](references/hardening-patterns.md#destructive-operations-on-derived-paths). Worked code: [security checklist](references/security-checklist.md).

### Rate limiting

Review limits at the affected API/auth boundary against existing policy, traffic and denial-of-service risks; example numbers are not project thresholds. With multiple processes, in-memory counters can multiply effective limits or reset on serverless; inspect the current shared enforcement before proposing a scoped change.

Pattern: [Rate limiting](references/hardening-patterns.md#rate-limiting).

### Secrets

Secrets use the existing environment/configuration owner, never source literals. Keep real credentials out of tracked files and preserve intentional placeholder templates. When a commit is separately authorized, inspect the staged diff for secrets. **Treat an exposed secret as compromised: report it to the credential owner for authorized rotation and incident handling. History rewriting needs separate authority and is not an automatic review action.**

Pattern: [Secrets management](references/hardening-patterns.md#secrets-management).

### Dependencies and supply chain

This is review guidance, not authorization to bootstrap, install, commit, upgrade or alter lockfiles. Use the owning environment and existing repository commands. If a policy change is needed outside scope, report it.

1. **Find the installation boundary and manager.** Use the workspace root that owns the lockfile, or an independent nested project only when it is outside that workspace. Corroborate `packageManager` (when present), the lockfile, and CI; investigate disagreement or competing lockfiles before dependency work. Preserve the pinned manager version.
2. **Review dependency scripts before authorized first execution.** Inspect the exact source and pinned manager's existing policy; do not blanket-approve. Propose a narrow policy repair if needed, but do not add installs, commits or manager upgrades to a security review.
3. **Use required repository audit gates when execution is in scope.** Triage critical/high by **reachability** (runtime, build, test, deploy paths) and fix availability. Never apply forced remediation (`npm audit fix --force` or equivalent) automatically, since forced fixes may cross declared dependency ranges; within authorized dependency work, preview, read changelogs and test each upgrade. Report any deferral and proposed review date without automatically creating tracker changes.
4. **Audits only match known advisories.** They do not catch a newly malicious or typosquatted package (`cross-env` vs `crossenv`). Review new dependencies, lockfile diffs, and script-policy changes together: ownership, maintenance, release age, provenance, transitive graph. Verify registry signatures where supported (`npm audit signatures`, `pnpm audit signatures`) and treat their absence as a signal to investigate, not automatic proof of compromise (A06, LLM03).

Triage decision tree: [Dependency audit triage](references/hardening-patterns.md#dependency-audit-triage). Manager matrix and install-script gate: [security checklist](references/security-checklist.md).

### Personal data and privacy

Hardening asks "can an attacker read it?" Privacy asks "should *we* hold it at all, and for how long?" The cheapest data to protect, breach, and comply over is the data you never collected; treat personal data as a liability to minimize.

- **Classify fields as you add them** (non-personal, PII, sensitive) and handle each class accordingly. You cannot protect, or honor a deletion request for, data you cannot find.
- **Collect only against a stated purpose.** "Might be useful later" is latent breach scope, not a purpose. Keep PII out of telemetry (the `observability-and-instrumentation` skill makes the same point from the ops side).
- **Set retention up front, then actually delete.** Every personal-data store needs a TTL and a working deletion path, including backups, caches, search indexes, and analytics copies.
- **Support the data-subject rights your jurisdiction requires** (GDPR, CCPA, and kin): export, correct, delete. Design the schema so a user's data is findable and erasable, not smeared irreversibly across systems.
- **Consent gates collection and third-party sharing, and is auditable.** Sending PII to an analytics, ad, or LLM vendor is sharing; the vendor needs a data-processing agreement. Make region a configurable policy, not a hardcoded assumption.

Classification table: [Data classification](references/hardening-patterns.md#data-classification). For an actual privacy incident, use the organization's incident/legal process and the existing [diagnosis workflow](../systematic-debugging/SKILL.md) within authorized scope; this reference does not determine jurisdiction-specific obligations.

### AI / LLM features

Calling an LLM — chatbots, summarizers, agents, RAG — adds a new attack surface; map it to the [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/):

- **Model output is untrusted input** (LLM05). Never into `eval`, SQL, a shell, `innerHTML`, or a file path; parse defensively, validate against a schema, then encode.
- **Prompts can be hijacked** (LLM01). Untrusted text in the context — a user message, a fetched page, a PDF — can carry instructions. The system prompt is not a security boundary; enforce permissions in code.
- **Keep secrets, other tenants' data, and the full system prompt out of the context window** (LLM02, LLM07); scope tool permissions, validate every tool argument, and enforce the existing authorization/confirmation boundary for destructive actions (LLM06); cap tokens, request rate, and recursion depth (LLM10); partition RAG embeddings per tenant and validate documents before indexing (LLM08).

Pattern: [LLM output handling](references/hardening-patterns.md#llm-output-handling).

## Review Checklist

For the affected trust boundaries, walk applicable sections of [security checklist](references/security-checklist.md): it covers authentication, authorization, input, data protection and privacy, headers and CORS, dependencies and supply chain, AI/LLM, and error handling, plus the OWASP quick-reference tables.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is an internal tool, security doesn't matter" | Internal tools get compromised. Attackers target the weakest link. |
| "We'll add security later" | Security retrofitting is 10x harder than building it in. Add it now. |
| "No one would try to exploit this" | Automated scanners will find it. Security by obscurity is not security. |
| "The framework handles security" | Frameworks provide tools, not guarantees. You still need to use them correctly. |
| "It's just a prototype" | Prototypes become production. Security habits from day one. |
| "Threat modeling is overkill here" | Five minutes of "how would I attack this?" prevents the design flaws no control can patch later. |
| "It's just LLM output, it's only text" | That "text" can be a SQL statement, a script tag, or a shell command. Treat it like any untrusted input. |
| "The audit passed, so the dependency is safe" | Audits match known advisories. They do not detect a newly malicious package or make unreviewed install scripts safe to execute. |
| "Collect it now, we might need it later" | Data you don't hold can't be breached, subpoenaed, or mis-deleted. "Might need it" is breach scope, not a purpose. |
| "We'll handle deletion requests manually" | Manual erasure misses backups, caches, and analytics copies. If the schema can't find a user's data, you can't honor the request — design for it. |
| "Compliance is legal's problem, not ours" | Export, deletion, retention, and consent are schema and code. Legal can't bolt them on after you've smeared PII across ten systems. |

## Red Flags

- User input passed directly to database queries, shell commands, or HTML rendering
- A delete, move, or overwrite whose target comes from a payload, a config value, or another process's command line, guarded only by a shape check on the path
- Secrets in source code or commit history
- API endpoints without authentication or authorization checks
- Missing CORS configuration or wildcard (`*`) origins
- No rate limiting on authentication endpoints, or an in-memory limiter in front of more than one instance
- Stack traces or internal errors exposed to users
- Dependencies with known critical vulnerabilities, competing lockfiles at one installation boundary, non-reproducible installs, or blanket-approved scripts
- Server fetches user-supplied URLs without an allowlist (SSRF)
- LLM/model output passed into a query, the DOM, a shell, or `eval`
- Secrets, PII, or the full system prompt placed inside an LLM context window
- Personal data collected with no stated purpose, retention limit, or deletion path
- PII sent to analytics/ad/LLM vendors with no consent or data-processing agreement
- "Delete my account" that only flips a flag while the personal data lingers in stores and backups

## Verification

After implementing security-relevant code, check applicable controls using permitted offline tests and existing package gates. Mark non-applicable items and omitted live checks explicitly:

- [ ] Required owning-package audit results are reviewed for reachable critical/high findings; lockfile and script-policy risks are reported, without unauthorized CI/dependency changes
- [ ] No secrets in source code or git history
- [ ] All user input validated at system boundaries
- [ ] Destructive filesystem operations resolve symlinks, then verify allowlisted root, minimum depth, and ownership before running
- [ ] Authentication and authorization checked on every protected endpoint
- [ ] HTTP/browser controls in scope are checked through permitted response tests; no browser launch is implied
- [ ] Error responses don't expose internal details
- [ ] Relevant auth rate limits are checked against current policy and shared enforcement, where present
- [ ] Relevant server fetches use the owning endpoint admission/allowlist and cannot be redirected to unintended targets
- [ ] LLM/model output validated and encoded before use (if AI features present)
- [ ] Personal data is classified, minimized to a stated purpose, and has a retention limit
- [ ] Deletion and export requests work end-to-end (including backups, caches, and analytics copies)
