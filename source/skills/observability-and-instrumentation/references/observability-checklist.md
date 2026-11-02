# Observability Checklist

Quick reference for requested instrumentation. Use alongside [observability-and-instrumentation](../SKILL.md); check only applicable signals, reuse the existing stack and report omissions. This checklist does not authorize dependencies, format/protocol migrations, live operations or hardware access.

## Table of Contents

- [On-Call Questions (Start Here)](#on-call-questions-start-here)
- [Structured Logging](#structured-logging)
- [Metrics](#metrics)
- [Distributed Tracing](#distributed-tracing)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Verify the Telemetry](#verify-the-telemetry)
- [Scoped Completion](#scoped-completion)

## On-Call Questions (Start Here)

Telemetry without a question is noise. Before instrumenting anything:

- [ ] The concrete diagnostic questions for the affected behavior are written down
- [ ] Every signal below maps to one of those questions
- [ ] Each question is matched to the right signal type: metrics say **that** something is wrong, traces say **where**, logs say **why**

## Structured Logging

- [ ] Changed logs preserve the configured format and expose stable events/useful fields; JSON is optional
- [ ] Related events retain the existing request/report/attempt correlation; new caller values are validated/bounded
- [ ] Supported correlation crosses relevant existing boundaries; wire/schema changes need explicit scope and consumer updates
- [ ] Any log stream written by more than one entry point (scheduler, replay endpoint, manual run) carries an entry-point field, set where the run starts and propagated alongside the correlation ID
- [ ] Log levels are consistent: `error` = invariant broken, someone may act; `warn` = degraded but handled; `info` = significant business event; `debug` = off in production
- [ ] No secrets, tokens, passwords, or unredacted PII in any log line (hard rule from `security-and-hardening`)
- [ ] Fields are allowlisted — no whole request/response bodies, no auth headers
- [ ] External service calls logged with metadata only: endpoint, status, latency, attempt count, sanitized identifiers
- [ ] Actual log output spot-checked: structured fields, not `[object Object]`

## Metrics

- [ ] Metrics in scope use relevant **RED** signals: Rate, Errors, Duration
- [ ] Resource metrics in scope use relevant **USE** signals: Utilization, Saturation, Errors
- [ ] Latency distributions/percentiles are used where they answer the question; averages alone do not establish tail behavior
- [ ] All labels come from small, fixed sets (route template, status class, provider name)
- [ ] No unbounded label values: no user IDs, tenant IDs, emails, raw URLs, request IDs, or error message text
- [ ] Status dimensions use the existing bounded convention; class versus exact code is a diagnostic/cost choice
- [ ] Queue depth/processing duration tracked where those signals are in scope and useful

## Distributed Tracing

Optional: only when tracing is requested or a demonstrated gap warrants it. Reuse the selected stack; no new SDK/exporter/vendor is implied.

- [ ] Existing tracing initializes in its owning startup path and has observable failure/shutdown/flush handling
- [ ] Existing instrumentation coverage is reviewed for the affected HTTP, gRPC or DB calls
- [ ] Trace context is preserved across supported affected calls without implicitly changing native transport/wire contracts
- [ ] Context survives relevant async boundaries within existing message contracts
- [ ] Manual spans only around meaningful internal units of work, with the attributes on-call will filter by
- [ ] No secrets or PII as span attributes
- [ ] Sampling, retention and cost bounds follow the existing policy; full error retention is not automatic

## Alerting

- [ ] Alerts in scope use actionable symptoms or evidenced impending capacity/safety risk, following existing operational policy
- [ ] Noisy/self-healing alerts are reviewed with their owner; no automatic deletion of existing safety/operational alerts
- [ ] Every alert links to a runbook — minimum three lines: what it means, first query to run, escalation path
- [ ] Thresholds and durations justified by an SLO or historical data, not guesses
- [ ] Severity and escalation reuse current policy; page/ticket are examples, not a required migration
- [ ] Alert-rule fixtures use fake/dry-run notification sinks and valid runbook links; live firing needs separate authority
- [ ] No alerts that fire daily and get acknowledged without action

## Dashboards

Only if dashboards are in scope; use existing tools rather than installing a new stack.

- [ ] Relevant service health signals are visible: error rate, latency, traffic or saturation
- [ ] Dependency health panel shows per-service error rates and latency
- [ ] Dashboard answers the on-call questions from the top of this checklist — not "everything except the answer"
- [ ] Default time range is sensible (1h–6h, not 30d)

## Verify the Telemetry

Instrumentation is code; it can be wrong. Use permitted offline fakes/fixtures, captured
logs and isolated collectors; guidance-only work remains static:

- [ ] Relevant error/timeout/retry/cancellation fixture found through existing correlation
- [ ] Metric samples have expected labels/values and bounded cardinality, if metrics are in scope
- [ ] Trace fixtures preserve supported context and lifecycle, if tracing is in scope
- [ ] Redaction and entry-point attribution are checked on actual permitted output
- [ ] Any live/deployment/physical checks are explicitly omitted unless separately authorized and observed

## Scoped Completion

Before claiming instrumentation complete, check only the signals required by the task:

- [ ] Each diagnostic question maps to evidence in existing or scoped new signals
- [ ] Changed logging preserves consumers, secrets policy and correlation
- [ ] Optional metrics/traces/alerts have focused offline evidence, or are explicitly out of scope
- [ ] Relevant current runbooks are updated when documentation is affected
- [ ] Required owning-package application checks passed when execution is authorized

Launch traffic, staging fault injection, live alert notifications, tracing UIs and robot
actions are not implied. Use the owning runbook and separate authority for deployment
operations; do not load an unavailable shipping skill or infer physical success.
