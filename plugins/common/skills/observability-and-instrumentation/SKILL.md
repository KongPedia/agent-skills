---
name: observability-and-instrumentation
description: Design, add or review logging, metrics, tracing or alerting for a concrete diagnostic gap. Use when those signals are requested or needed to explain a measured failure; not every production feature, routine prose change or an automatic telemetry-stack migration.
---

# Observability and Instrumentation

## Overview

Code you can't observe is code you can't operate. Observability is the ability to answer "what is the system doing and why?" from the outside, using the telemetry the code emits. Plan observability alongside affected behavior, reusing existing signals first. Add only the missing evidence needed for the task; this is not a requirement for a new stack on every feature.

> Selectively vendored and adapted; [project adaptations](../../references/engineering.md#curated-source-adaptations) retain current logging, lifecycle, contracts and safety. See [provenance](../../provenance.json).

## When to Use

- Adding or reviewing requested telemetry for a production behavior
- An affected service, endpoint, job or integration has a concrete diagnostic gap
- A production incident took too long to diagnose ("we couldn't tell what happened")
- Setting up or reviewing alerting rules
- Reviewing whether affected I/O, retries, queues or cross-service calls remain diagnosable

**NOT for:**
- Root-cause diagnosis alone — use the existing [systematic-debugging](../systematic-debugging/SKILL.md) workflow; select this skill only if a telemetry gap is part of the task
- Profiling/optimization alone — use the owning measured-performance workflow, not an unimported skill dependency
- Launch/deployment operations — use the owning runbook and separate authority; this skill covers instrumentation, not permission to operate live systems

## Process

### 1. Define "working" before instrumenting

Telemetry without a question is noise. Before adding any instrumentation, write down the few concrete questions an on-call engineer will ask about this feature:

```
FEATURE: checkout payment retry
QUESTIONS ON-CALL WILL ASK:
1. What fraction of payments succeed on first attempt vs after retry?
2. When a payment fails permanently, why? (provider error? timeout? validation?)
3. Is the payment provider slower than usual?
→ Every signal below must help answer one of these.
```

If you can't name the questions, you're not ready to instrument — you'll log everything and learn nothing.

### 2. Pick the right signal for each question

| Signal | Answers | Cost profile | Example |
|---|---|---|---|
| **Structured log** | "What happened in this specific case?" | Per-event; grows with traffic | `payment_failed` with provider error code |
| **Metric** | "How often / how fast, in aggregate?" | Fixed per series; cheap to query | p99 latency of provider calls |
| **Trace** | "Where did time go across services?" | Per-request; usually sampled | One slow checkout, broken down by hop |

Rule of thumb: metrics tell you **that** something is wrong, traces tell you **where**, logs tell you **why**.

### 3. Structured logging

Prefer stable events and useful fields through the existing logger and configured format. JSON is an option, not a project-wide mandate; preserve current sinks, levels and consumers. This TypeScript example illustrates event/field separation, not a new logger dependency:

```typescript
// BAD: string interpolation — unqueryable, inconsistent
logger.info(`Payment ${id} failed for user ${userId} after ${n} retries`);

// GOOD: stable event name + structured fields
logger.warn({
  event: 'payment_failed',
  paymentId: id,
  provider: 'stripe',
  errorCode: err.code,
  attempt: n,
}, 'payment failed');
```

**Log levels — use them consistently:**

| Level | Meaning | On-call action |
|---|---|---|
| `error` | Invariant broken; someone may need to act | Investigate |
| `warn` | Degraded but handled (retry succeeded, fallback used) | Watch for trends |
| `info` | Significant business event (order placed, job finished) | None |
| `debug` | Diagnostic detail | Off in production by default |

**Preserve existing correlation.** Reuse the request/report/attempt identifiers already owned by the boundary. If a diagnostic gap needs new local correlation, validate/bound any caller-supplied value and avoid raw secrets or PII. Do not change wire headers, schemas or transport contracts without scope. The following Express example applies only to a compatible HTTP boundary:

```typescript
// Express: child logger per request, ID propagated downstream
app.use((req, res, next) => {
  // Illustrative validated ID helper; use the existing boundary's bounded parser.
  req.id = validatedRequestId(req.headers['x-request-id']) ?? crypto.randomUUID();
  req.log = logger.child({ requestId: req.id });
  res.setHeader('x-request-id', req.id);
  next();
});
```

**When several entry points write to one log, name the entry point.** A correlation ID identifies a run; it does not say which code path started it. The same job reached by a scheduler, by a replay endpoint, and by a manual CLI run produces interchangeable lines in one sink, so attributing a line falls back to elimination — cross-reading the scheduler's history, the process table, a deploy log — and that argument holds only as long as those external records happen to still exist. Stamp the entry point where the run starts, next to the correlation ID, and propagate both the same way:

```typescript
// One helper for every entry point: the run's own logger carries both fields.
// `entryPoint`, not `source` — ECS reserves `source.*` for network fields.
export const runLog = (entryPoint: 'scheduler' | 'replay_endpoint' | 'cli', runId: string) =>
  logger.child({ entryPoint, requestId: runId });

// scheduler tick        -> runLog('scheduler', crypto.randomUUID())
// POST /jobs/:id/replay -> runLog('replay_endpoint', req.id)
// CLI invocation        -> runLog('cli', process.env.RUN_ID ?? crypto.randomUUID())
```

Where the existing contract permits it, retain entry-point attribution across the same boundaries as correlation. A wire/schema change needs explicit scope and all active consumers updated; otherwise keep attribution in the owning local logger. A field that merely correlates with an entry point is a hint, not an attribution: anything that can invoke the job can reproduce it.

**Never log secrets, tokens, passwords, or full PII.** This is a hard rule from the `security-and-hardening` skill — telemetry pipelines are a classic data-leak path. Allowlist fields; don't log whole request bodies.

### 4. Metrics

For requested request-driven metrics, use **RED** to choose relevant signals: **R**ate (requests/sec), **E**rrors (failure rate), **D**uration (latency histogram, not average). For resources (queues, pools, hosts), use **USE**: **U**tilization, **S**aturation, **E**rrors.

Reuse the existing metrics API/backend. The example below uses Prometheus' `prom-client` only to illustrate bounded dimensions; it does not authorize a new dependency, exporter, vendor or OpenTelemetry rollout.

```typescript
import { Histogram } from 'prom-client';

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route', 'status_class'],  // '2xx', not '200'
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});
```

**Cardinality is the failure mode.** Every unique label combination is a separate time series. Labels must come from small, fixed sets (route template, status class, provider name). Never use user IDs, raw URLs, error messages, or other unbounded values as labels — that belongs in logs and traces.

```
OK as label:    route="/api/tasks/:id"   status_class="5xx"   provider="stripe"
NEVER a label:  user_id, email, request_id, full URL, error message text
```

When latency distributions answer the diagnostic question, prefer a histogram and inspect percentiles: an average alone can hide tail failures. Keep useful existing aggregates and avoid adding histograms where their cost or resolution is not justified.

### 5. Distributed tracing

Tracing is optional: use it when logs/metrics cannot answer the cross-boundary question and the task includes tracing. Reuse the existing stack. If OpenTelemetry is already selected, the illustrative setup below shows initialization ordering, not authorization to install it or blanket-enable instrumentation. Preserve startup failure, shutdown/flush ownership and redaction:

```typescript
// Illustrative existing-OTel setup only; integrate into the current lifecycle owner.
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  serviceName: 'checkout-service',
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start(); // Owner must handle startup errors and await sdk.shutdown() on teardown.
```

Add manual spans only around meaningful internal units of work (e.g., `applyDiscounts`, `chargeProvider`) and attach the attributes on-call will filter by. Within supported contracts, preserve context across relevant async boundaries; report unsupported wire propagation rather than changing protocols implicitly. Choose sampling, retention and cost bounds from the existing policy; full error retention is not automatic.

### 6. Alerting

Alert on **symptoms users feel**, not on causes:

```
SYMPTOM (page-worthy):           CAUSE (dashboard, not a page):
error rate > 1% for 5 min        CPU at 85%
p99 latency > 2s                 one pod restarted
queue age > 10 min               disk at 70%
```

Prefer user-visible symptoms for paging; cause signals can still warn of impending capacity or safety problems. Choose rules from evidence and existing operational policy, not a universal alert taxonomy.

Rules for every alert you create:

1. **It must be actionable.** If it routinely self-heals without action, propose tuning or retirement with the owner; do not delete existing safety/operational alerts without scope.
2. **It links to a runbook** — even three lines: what it means, first query to run, escalation path.
3. **It has a threshold and duration** justified by the SLO or by historical data, not by a guess.
4. Reuse existing severity and escalation policy. **Page** (act now) and **ticket** (planned follow-up) are useful examples, not a required two-tier migration.

#### Writing Runbooks

Rule 2 above requires every alert to link to a runbook. A runbook's job is to answer three questions without requiring the reader to think: what is happening, what to check first, and who to call if that doesn't resolve it. Update the appropriate existing `docs/runbooks/` page when documentation is in scope; add a new page only for a distinct runbook need.

**Minimum viable runbook (three lines):**

```markdown
# Runbook: High Error Rate on /api/tasks
**Means:** DB connection pool likely exhausted, or a bad deploy.
**First check:** `SELECT count(*) FROM pg_stat_activity WHERE backend_type = 'client backend';`
  — if count > pool limit, see Step 2. (Swap in the equivalent for your database.)
**Escalate to:** #db-oncall or engineering on-call rotation.
```

**When to expand beyond three lines:** add steps only when the first check alone isn't enough to decide. A five-step runbook that covers the three most common causes is better than a twenty-step document that covers every edge case and gets skimmed.

**Keep runbooks current.** Update the runbook as part of closing every incident it was used in — a stale runbook builds false confidence. If a step was wrong or missing, fix it before marking the incident resolved.

### 7. Verify the telemetry itself

Instrumentation is code; it can be wrong. Use permitted offline fixtures, fake clocks,
captured logs and isolated collectors to inspect actual output:

- Exercise success, failure, timeout, retry and cancellation paths relevant to the change.
- Check stable fields, current correlation, entry-point attribution, level and redaction.
- For metrics already in scope, inspect expected labels/values and bounded cardinality.
- For traces already in scope, inspect supported context and startup/shutdown behavior.
- For alert rules in scope, evaluate sample series through a fake/dry-run sink; do not
  lower live thresholds or send notifications merely to complete this checklist.

Staging traffic, tracing UIs, live alerts, deployments and robot actions require their
own requested scope and authority. Never connect to physical devices or hardware-connected endpoints, or
actuate movement, firing or recovery for telemetry validation. Guidance-only edits use
static checks, not application execution. Report live/deployment/physical evidence as
omitted unless separately authorized and actually observed.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add logging after it works" | "After" becomes "after the first incident", which is the most expensive moment to discover you're blind. Instrument as you build. |
| "More logs = more observability" | Unstructured noise makes incidents slower, not faster. Three queryable events beat three hundred prose lines. |
| "More structure always needs a new logger" | Existing logging can often carry stable event names and bounded fields; compare actual diagnostic value before adding a dependency or format migration. |
| "We can just look at the dashboards when something breaks" | Dashboards built without defined questions show you everything except the answer. Start from on-call questions. |
| "Alert on everything important, we'll tune later" | A noisy pager trains people to ignore it. The tuning never happens; the missed real page does. |
| "User ID as a metric label makes debugging easier" | It also makes your metrics backend fall over. High-cardinality lookups belong in logs and traces. |
| "Tracing is always necessary across two services" | Start with the question and existing evidence. Add spans only when the diagnostic gain justifies lifecycle, privacy and cost overhead within scope. |

## Red Flags

- A changed retry/queue/external path whose failure cannot be explained by existing or scoped new signals
- Log output whose event or useful fields cannot be recovered through the existing format
- Related request/report events cannot be correlated through existing identifiers
- One log stream fed by a scheduler, a webhook, and manual runs, with no field naming which one produced the line
- Metrics labeled with user IDs, raw URLs, or error message text (cardinality bomb)
- Latency tracked as an average with no percentiles
- Alerts that fire daily and get acknowledged without action
- Alerts on causes (CPU, memory) paging humans while user-facing error rate is unmonitored
- Secrets, tokens, or full request bodies appearing in logs
- "It works on my machine" as the only evidence a production feature is healthy

## Verification

After authorized instrumentation, confirm applicable items and report unimplemented/unverified optional signals explicitly:

- [ ] The on-call questions for this feature are written down, and each signal maps to one
- [ ] Changed logs use the existing format with stable events, useful bounded fields and supported correlation
- [ ] Affected shared log sinks preserve useful entry-point attribution where needed; wire propagation remains inside supported contracts
- [ ] No secrets, tokens, or unredacted PII in any log line (spot-check actual output)
- [ ] Metrics in scope answer the stated questions with bounded labels; no new stack is implied
- [ ] Where distributions are relevant and supported, latency percentiles are inspectable
- [ ] Traces in scope preserve supported context and lifecycle in offline/isolated evidence
- [ ] Alert rules in scope are actionable and evaluated offline with a valid runbook/escalation reference
- [ ] Relevant failure fixtures can be explained by captured signals; no staging fault injection is implied

For the scoped at-a-glance version, see [observability checklist](references/observability-checklist.md).
