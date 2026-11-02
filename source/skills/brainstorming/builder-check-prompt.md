# Builder Check Prompt

Adapted from the pinned Superpowers resource: use only when an independent design-readiness check is useful and
authorized. It does not force delegation or a new approval round for every task.

```text
Read [DOCUMENT_PATH] as the person who will implement [DOMAIN / OUTCOME].
Stay within the task's scope; do not edit, run applications or recursively delegate.
Report only missing decisions whose wrong answer would materially change implementation or acceptance.
For each, give the question, supporting document location and impact; rank by importance.
Skip decisions explicitly left to the builder, reversible defaults you can reasonably choose, and wording nitpicks.
Distinguish already-answered findings from true gaps. If nothing important remains, say so with the review limits.
```
