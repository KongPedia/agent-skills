# Opt-in agent behavior evaluations

These evaluations belong to **agent-skills**, not `project-blueprints`. Blueprint rendering/selection/update checks
stay in its deterministic suite; do not duplicate the model runner there. Python reuses maintainer tools, not a
required language or runtime for skill consumers.

| Location | Purpose | Model calls? |
| --- | --- | --- |
| `evals/tasks/`, `fixtures/`, `checks/` | Fixed requests, starting code and independent outcomes | Never alone |
| `scripts/run_host_evals.py` | Existing-login Codex/project-skill comparison; Docker only grades | Yes |
| `scripts/run_evals.py` | Optional full-container Codex/Claude plugin comparison | Yes |
| `evals/graders.py`, `evals/drive_check.py`, `evals/protocol.json` | Conservative checks and frozen experiment definition | Never |
| `tests/test_eval_*.py`, `tests/test_host_evals.py` | Evaluator regressions, including known-good/bad candidates | Never |

## Initial cases

- `python-tdd`: integer balance deduction, validation and test-first evidence review.
- `fastapi-lifecycle`: request resource acquisition/cleanup, including failures.
- `api-boundary`: response schema, missing user and private-field exclusion.
- `simple-script`: stdlib operation with irrelevant FastAPI/robotics skills available as a negative control.
- `docs-only`: bounded README change; commands excluded and complete input supplied in the prompt.
- `readonly-analysis`: diagnosis with changes/commands excluded and complete input supplied in the prompt.

Tasks declare selected bundles, canonical `bundle:skill` IDs, runtime modules, allowed file changes and named checks.
The negative control is deliberate, not Copier's normal Python-profile selection. These six tasks do not cover all
41 skills. Checkers stay outside the agent's writable workspace.

## Default: existing-login model, isolated grader

The host runner uses existing Codex authentication without copying it or installing host plugins. **Only automated
outcome grading runs in Docker**: network disabled, workspace/checks read-only, non-root, resource-limited and without
provider credentials. The grader needs neither model CLIs nor provider login.

Build the Python-only default `grader` target from the small `evals/` context, not the repository root:

```bash
docker build -f evals/Dockerfile -t konglabs-agent-evals:grader evals/
```

This target uses Python 3.13 with pinned FastAPI/httpx, not Node or agent CLIs. Review the base image and dependencies;
for reproducible builds also pin the target's base-image argument to a reviewed digest. Transitive dependencies are
not a fully locked supply chain. Runners resolve reviewed existing images to immutable IDs and never pull/build them
implicitly. The new lightweight target does not change the image IDs recorded in historical results.

From the repository root, with an existing authenticated Codex compatible with the inspected `0.164.0` controls:

```bash
uv run --locked --with fastapi==0.162.0 --with httpx==0.28.1 \
  python scripts/run_host_evals.py \
  --codex-bin /opt/homebrew/bin/codex --model gpt-6.1-sol \
  --candidate . --baseline vanilla --trials 3 --jobs 2 --timeout 240 \
  --grader-image konglabs-agent-evals:grader \
  --output .eval-results/codex-project-skills-comparison
```

Output must be new. Omit `--task` for all six or repeat it for selected IDs. `--jobs` permits one or two concurrent
pairs; paired arms stay sequential and alternate order across trials. There are no automatic trial retries.

Both arms receive identical task prompts, model, medium reasoning, initial fixture and wall-time budget. Candidate
copies complete generated bundle snapshots to `.agents/skills/<bundle>/`, preserving resources/references and
namespaces for native project-local loading. There is no candidate-only “use this skill” prompt. `vanilla` supplies no
project skills; a reviewed prior checkout can replace it for version comparisons. Evaluated payloads are actual
`plugins/` bytes, not unbuilt source edits. Do not overwrite global plugin caches or user-registered sources.

The runner disables inventoried ambient skills by exact `SKILL.md` paths, including resolved aliases, not directories
or names. The inspected host used 56 selectors. Native instructions remain enabled; the experimental discovery-skip
flag is not used. The offline `python-tdd` gate showed no baseline project skills and only expected common/python
candidate catalogs. This evaluates project-skill loading, not plugin installation/runtime or marketplace/App discovery.

### Safety and evidence limits

- Existing global `AGENTS.md`, managed/session policy, caches and authentication can remain common to both arms.
  `vanilla` means **no project skills**, not a pristine machine.
- Host workspace-write sandboxing limits writes, not all reads or credential access. Plugins/hooks/apps/multi-agent
  are disabled; shell environment and network are restricted. Use trusted fixtures and keep artifacts private.
  The CLI still needs its authenticated model connection. Version-sensitive controls require review after upgrades;
  macOS cache-write warnings are not automatically task failures—inspect exit/events.
- Grading generated Python runs in credential-free Docker, not the authenticated host process. A trusted outer driver
  requires normal completion and exactly the expected criteria, blocking simple printed-marker/early-exit spoofing.
  Same-interpreter assertions are not tamper-proof against hostile Python.
- Ordinary Docker is not Docker Sandboxes/`sbx`: no per-agent microVM or credential proxy. It does not protect against
  malicious kernels/daemons or unbounded host disk writes. Temporary workspaces are bind mounts; artifact-size limits
  bound retained output, not all possible trial writes. Stronger adversarial work needs a hardened environment.

## Frozen protocol and reports

The [frozen protocol](../evals/protocol.json) fixes the question, task/fixture/checker hashes, settings, metrics and
rules before results. Six tasks × three trials × two arms schedule **36 calls**: per arm, 15 externally checkable
code/document outcomes and three read-only answers requiring separate semantic review. Do not combine those review
answers with the automated denominator. Preserve zero/negative results; do not tune prompts or graders after seeing
outcomes. Prescriptive tasks can have ceiling effects. Measurement completion does not mean positive effect or A+.

All selected fixtures, provider bundle dependencies/skill IDs, CLI and grader-image dependencies are preflighted
before paid calls/output creation. Reports retain actual payload/fixture/prompt/checker/driver/runner/protocol hashes,
CLI version, image ID, disabled ambient paths, global-guide hash, commands, raw traces, normalized events, before/after
hashes, diffs, grader results, usage/time and cleanup. No CLI billing fields are invented.

The host runner updates `eval_report.json` after completed pairs and writes `provenance.json`. The full-container
runner updates after trials and writes `setup_error.json` for setup failures after output exists. Reports can be
partial after interruption. Environment/timeout/grading/cleanup failures stay separate from outcome failures;
unconfirmed agent termination blocks grading. Inspect failed container cleanup rather than assuming safe completion.

| Evidence | Interpretation |
| --- | --- |
| Outcome | External checker pass/fail; read-only semantic answers require separate transcript review |
| Scope | Final artifact hash changes, including deletion; transient writes may be missed |
| Reads | Successful native Claude Skill/Read or conservative literal known-path reads, not adherence |
| Docker Codex cache | Exact installed paths are SHA-256-attested against provider bytes before crediting reads |
| TDD | Automated chronology stays unknown without independent intermediate snapshots; transcript observations separate |
| No commands | Observed commands can establish violation; absence cannot prove none occurred |

Missing/unrecognized reads stay `unknown`. Installation, discovery, reading, adherence and outcome are distinct.
No F1 from incomplete traces, arbitrary combined score or population reliability claim. One CLI session may internally
retry within its budget: this is **task-run success**, not first-test-pass rate.

Exit 0 means completed trials with no observed failure, not that unknowns passed. Exit 1 indicates a trial/outcome or
observed behavior failure, including baseline failures; it is not an automatic candidate-release gate. Exit 2 means
setup/argument failure. No model evaluation is added to PR CI; there are no automatic commits or publication.

## First experiment: explicit requests, no positive effect demonstrated

The [sanitized aggregate](../evals/reports/codex-host-2026-10-27.json) records the 2026-10-27 comparison with host Codex
`0.164.0`, `gpt-6.1-sol`, medium reasoning: **36 attempted calls, 34 completed, two timeouts**, one per arm. Timeout
causes remain unconfirmed; no retries hide them. Historical grader image IDs remain unchanged in the aggregate.

| Metric | No project skills | Candidate project skills |
| --- | --- | --- |
| External outcome passes / scheduled | 14/15 | 14/15 |
| External outcomes unknown (timeout) | 1 | 1 |
| Read-only answers correct, transcript review | 3/3 | 3/3 |
| Observed RED→implementation→GREEN, transcript review | 3/3 | 3/3 |
| Strict automated TDD verdict | Unknown | Unknown |
| Final-artifact scope checks | 18/18 pass | 18/18 pass |
| Reported input tokens, 17 reporting trials each | 883,495 | 1,362,684 |

Thirteen comparable outcome pairs were unchanged: zero improved and zero regressed. Five pairs remain unknown:
two timeout-affected API pairs and three manual semantic pairs outside automated outcomes. Scope has 16 comparable
pairs, all unchanged. Known external outcomes were 14/14 each; retain the 15 scheduled denominator too.

Candidate reported input usage was **54.24% higher**: observed CLI usage, not currency cost or statistical proof.
Actual skill-file reads were observed. A separate conservative parser replay improved read observation only; original
captures/outcomes remain preserved. Read counts are lower bounds, not discovery precision/recall or adherence proof.

**Measurement is complete; improvement was not demonstrated. The original 90+/A+ effectiveness goal is unmet.**
Six small, prescriptive cases may have ceiling effects; common host policy makes this conditional evidence. Do not
generalize to all skills, native plugin runtime, Codex App or Claude, which has no real model trials here. Earlier
smoke was integration evidence only. An initial pilot was excluded for grader-isolation repair, not outcome selection;
frozen evaluation inputs were unchanged. Raw private evidence remains under
`.eval-results/codex-project-skills-final-20261027/`, not included in a fresh checkout.

## Follow-up: implicit requests, observed process improvement

The separate [frozen follow-up protocol](../evals/followup/protocol.json) and
[aggregate report](../evals/reports/codex-implicit-2026-10-27.json) preserve the first experiment unchanged. Four
requests cover atomic inventory reservations, TTL idempotency, request-resource failures and nested public API
schemas. None asks for TDD, test-first execution or a named skill. Three repetitions per task and condition completed
**24 actual Codex CLI sessions**, with the same `0.164.0` client, `gpt-6.1-sol`, medium reasoning and 360-second budget.

| Metric | No project skills | Unchanged project-skill bundles |
| --- | --- | --- |
| Observed test-first process, scheduled denominator | 0/12 | 11/12; one unknown |
| External all-criteria outcome success | 12/12 | 12/12 |
| Final-artifact scope | 12/12 pass | 12/12 pass |
| Reported input tokens | 842,910 | 1,490,304 (+76.8%) |
| Median trial elapsed time | 45.954 s | 62.085 s (+35.1%) |

Two independent native-agent reviewers scored condition-masked command/file-change transcripts against the
predeclared rubric: relevant test edit → meaningful assertion RED → first implementation edit → same tests GREEN,
without visible weakening. They agreed on all 24 verdicts. One candidate API trial changed tests alongside the
implementation after RED; unavailable intermediate test contents leave that verdict **unknown**, not passed.
The observed-process improvement remains **+91.67 to +100 percentage points** under the declared unknown bounds.
Automated strict TDD remains unknown because independent intermediate runtime snapshots were not captured.

This demonstrates a **local observed test-first process benefit**, not better final-code correctness: all 12 outcome
pairs were unchanged. Input tokens are reported CLI usage, not currency cost. Four task clusters with repeated trials
do not establish population significance, universal skill effectiveness, an isolated single-skill effect or A+.
Existing host policy remains common to both arms; candidate bundles staged 25 or 27 actual skill files, while baseline
staged none. Skills, generated payloads and licenses were unchanged. No real Claude calls were made.

Reproduce only as an explicitly budgeted model evaluation with a **new** output directory:

```bash
uv run --locked --with fastapi==0.162.0 --with httpx==0.28.1 \
  python scripts/run_host_evals.py --codex-bin /opt/homebrew/bin/codex \
  --model gpt-6.1-sol --tasks-dir evals/followup/tasks \
  --protocol evals/followup/protocol.json --candidate . --baseline vanilla \
  --trials 3 --jobs 2 --timeout 360 --grader-image konglabs-agent-evals:grader \
  --output .eval-results/codex-implicit-skills-comparison
```

Inputs and rubric were frozen before model runs. One dependency-only preflight amendment, recorded in the protocol,
added FastAPI's required `api-contracts` bundle before any model call; no prompts/checkers changed after results.
All 18 frozen input hashes remained unchanged during execution. Original traces, masked review packets, both reviews
and captured repository inputs remain private under `.eval-results/codex-implicit-skills-20261027/` and
`.eval-results/implicit-followup-preflight/`; sanitized per-trial verdicts and evidence hashes are in the aggregate.

## Workflow axes: SDD, source-grounded work and DDD

The [third frozen protocol](../evals/workflows/protocol.json) evaluates seven additional cases with unchanged
common/python bundles: shared-protocol SDD plus a small-fix negative control, SDK unit repair plus an evidence-only
source diagnosis, cancellation/refund ownership, an active competing-domain-model proposal and a local-label
negative control. “Source-first” here means grounding work in supplied code/contracts, not a standardized methodology
or a claim to test every upstream source. There is no named source-dd skill in this experiment.

Seven cases × three repetitions × two arms attempted **42 Codex CLI sessions**, using the same host client/model,
medium reasoning and a 360-second budget. Fifty-eight repository inputs and the full plugin tree were frozen before
execution. Two independent native reviewers judged masked visible actions and full final artifacts against the
predeclared per-case rubric, not document presence, class counts or skill-read counts. Skill/condition names were
masked; behavior can reveal a condition, so this is not guaranteed double-blinding. All three axes use a semantic
workflow endpoint separate from external code/artifact checks. Positive requests and negative ceremony controls
must remain distinct. Repetition within seven fixtures is not population significance or isolated-skill causality.

The [sanitized aggregate](../evals/reports/codex-workflows-2026-10-28.json) retains all 42 scheduled trials,
84 reviewer verdicts and per-criterion evidence. Both reviewers agreed on all verdicts. Results below are **semantic
workflow passes / scheduled per arm**, not an overall effectiveness score:

| Case | No project skills | Unchanged bundles | Interpretation |
| --- | --- | --- | --- |
| SDD shared-contract change | 0/3 | 0/3 | Neither arm recorded the complete required contract before implementation |
| SDD local-fix negative control | 3/3 | 2/3 + 1 unknown | No observed excess ceremony; parser-affected candidate stays unknown |
| Source-grounded SDK units repair | 3/3 | 3/3 | Correct in both arms; no incremental benefit demonstrated |
| Source evidence-only diagnosis | 3/3 | 3/3 | Evidence/uncertainty discipline in both arms |
| DDD cancellation/refund ownership | 3/3 | 3/3 | Correct boundaries/invariants in both arms |
| DDD active model proposal | 3/3 | 3/3 | Competing models and unresolved business choices handled in both arms |
| DDD local-label negative control | 3/3 | 2/3 + 1 unknown | No observed overarchitecture; capacity refusal stays unknown |

All six SDD positive trials eventually produced correct final artifacts but failed the distinct **contract-before-
implementation** endpoint: required compatibility/acceptance details were first recorded with production changes,
not beforehand. This is not proof that SDD “does not work”; the unchanged bundle did not improve that workflow in
this fixture. Other cases have ceiling effects. No case establishes a local workflow gain or regression under the
predeclared unknown bounds. The earlier TDD observed-process benefit remains separate, not transferable to these
axes or proof of better final code.

Confirmatory external outcomes were 18 pass/3 unknown for baseline and 17 pass/4 unknown for candidate; unknowns
include the invalid oracle and parser/capacity errors below, not demonstrated code failures. **17 comparable pairs
were unchanged, zero improved/regressed, four unknown.** Candidate reported input tokens were +65.10% over baseline
on the 20 matched pairs with usage available for both arms (1,789,164 vs 2,953,887); one capacity-affected pair lacked
candidate usage and was excluded from this descriptive usage comparison only. All 42 trials stay in workflow/outcome
denominators. Raw unequal-coverage totals (21 baseline vs 20 candidate) must not be treated as a matched cost delta.
Median elapsed time over 21 scheduled trials each was 37.251 s vs 49.351 s, including error attempts. These are CLI
usage/time observations, not billing or population performance estimates.

### Evaluation defects and recovery policy

The frozen run classified 40 sessions completed and two `agent_error`. One was a real provider-capacity refusal;
there was no retry or model switch. The other was an evaluator bug: Python `str.splitlines()` split a valid literal
U+2028 inside a JSON string, although JSONL records are LF-delimited. A [separate deterministic replay](../evals/reports/workflow-jsonl-audit-2026-10-28.json)
parsed the captured trace correctly and passed all four **unchanged** Docker outcome checks. Original status,
unknown confirmatory outcome and unknown primary review remain preserved; diagnostic recovery is not another model
trial or added confirmatory success. Parser repair is post-execution, not a silently changed frozen runner.
The shared runner was repaired after execution: LF-only JSONL framing and fallback secret-field redaction have
20 regression cases. Captured primary review packets were not regenerated, frozen results remain unchanged, and
no model calls were added for the repair. The frozen runner SHA-256 is recorded in the protocol; the repaired
runner SHA-256 is `fc6a29f1a0920dd89acca6bc054ac7de64e809dcf5519d93c4a4597b3072b56d`.
The one-off repair/test receipt remains private under `.eval-results/maintenance-receipts/`, not part of the
reusable benchmark or the committed effect evidence.

A [separate oracle-validity audit](../evals/reports/workflow-oracle-audit-2026-10-28.json) found that the local-label
checker required ValueError for nonstrings even though the public contract specified that exception only for
empty/overlong strings. Five completed implementations used TypeError; the sixth session was the capacity refusal.
**All six confirmatory outcomes are unknown/oracle-invalid symmetrically**, retaining raw failures separately.
A narrower posthoc publicly specified string-domain diagnostic passes for all five completed artifacts; it does
not replace the frozen grades or credit the capacity refusal. Negative-control complexity can still be reviewed
independently. Reference/checker self-checks shared this mistaken exception assumption, so passing calibration alone
had not established oracle validity; regression coverage now includes a distinct valid TypeError implementation.
Posthoc diagnostic scripts used an existing local grader tag and recorded its resolved image ID after grading; this
is weaker provenance than the primary runner’s pre-resolved immutable ID and is not a guarantee against concurrent
tag replacement. Future diagnostics should resolve the ID before running, without rewriting these receipts.

No real Claude trial was made: the host `claude` entry was a missing-binary shim, no dedicated evaluation key was
present, and the disposable image reported unauthenticated. No personal authentication was copied and no new login
was required. An existing authenticated Claude environment or dedicated evaluation credential remains necessary for
that separate lane. Codex results must not be presented as Claude evidence.

## Optional: run models inside containers

Use this separate lane for reviewed full-container Codex/Claude plugin comparisons. Build the `agent` target with
explicit pinned CLI versions; the default grader does not contain either CLI:

```bash
docker build -f evals/Dockerfile --target agent \
  --build-arg CODEX_VERSION=0.160.0 --build-arg CLAUDE_VERSION=2.1.118 \
  -t konglabs-agent-evals:agents evals/
```

Verify installed CLI versions in that image; local host help alone does not establish compatibility. Provision a
**dedicated, disposable, budget-limited** key through `KONGLABS_EVAL_CODEX_API_KEY` or `KONGLABS_EVAL_CLAUDE_API_KEY`
using a secret manager. Never paste keys into tasks, reports or Git. Only the selected key is forwarded under its
provider-native environment variable. No personal HOME/auth/config/cache/trust, Docker socket, MCP or host/user hooks
are mounted; optional session-guidance is not enabled. Generated model code can see the key: not credential isolation.
Known key text is redacted, but transformed secrets are not guaranteed redacted. Keep traces private and inspect them.

```bash
uv run --locked python scripts/run_evals.py \
  --engine codex --model "$CODEX_MODEL" --image konglabs-agent-evals:agents \
  --candidate . --baseline vanilla --task python-tdd \
  --timeout 300 --trials 1 --output .eval-results/codex-container

uv run --locked python scripts/run_evals.py \
  --engine claude --model "$CLAUDE_MODEL" --image konglabs-agent-evals:agents \
  --candidate . --baseline /path/to/reviewed-previous-agent-skills \
  --timeout 300 --trials 3 --output .eval-results/claude-regression
```

Model containers have bridge-network egress, not a provider-only allowlist. They are non-root, capability-dropped and
read-only outside bounded temporary HOME/workspace. Graders have no network or provider key. Both arms use fresh
HOME/config; Codex installs selected native plugins inside its container and Claude uses local `--plugin-dir` paths.
These differ from host project-skill copies and do not establish App/marketplace behavior. Vanilla has no provider
mount/plugins but still uses eval credentials; review the image for ambient instructions. Model defaults/upstream
behavior can change despite recorded IDs. This optional lane has no actual model-effectiveness result here.

## Verify the evaluator without model calls

Ordinary `uv run --locked pytest` remains offline and needs no Docker, keys or agent CLIs. Dependency-enabled checker
regressions use an isolated environment without changing the lock:

```bash
uv run --locked --with fastapi==0.162.0 --with httpx==0.28.1 pytest
uv run --locked python scripts/build_plugins.py --check
```

Docker integration remains opt-in. `KONGLABS_EVAL_IMAGE` selects the Python-only grader; optionally add
`KONGLABS_EVAL_AGENT_IMAGE` for full agent-CLI image checks. These tests do not call models:

```bash
KONGLABS_EVAL_IMAGE=konglabs-agent-evals:grader \
  uv run --locked --with fastapi==0.162.0 --with httpx==0.28.1 pytest tests/test_eval_docker.py
```

Evaluator tests, fake CLI orchestration and CLI version checks are not model behavior evidence.

## Primary references

- [OpenAI skill eval design](https://developers.openai.com/blog/eval-skills)
- [Codex non-interactive events](https://learn.chatgpt.com/docs/non-interactive-mode) and [security boundaries](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Claude CLI structured output/plugin directories](https://code.claude.com/docs/en/cli-reference)
- [Claude devcontainers](https://code.claude.com/docs/en/devcontainer) and [sandboxing](https://code.claude.com/docs/en/sandboxing)
- [Docker Sandboxes isolation, distinct from ordinary containers](https://docs.docker.com/ai/sandboxes/security/isolation)
- [Anthropic task/trial/grade separation](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
