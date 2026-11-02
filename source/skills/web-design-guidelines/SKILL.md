---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## Rule applicability

Require keyboard operability, not redundant event handlers. Preserve native `<button>` and `<a>` keyboard behavior;
add custom keyboard handlers only when the interaction needs behavior that native semantics do not provide. Do not
flag a native control solely for lacking `onKeyDown`/`onKeyUp`, or duplicate its activation through both key and click
handlers. Interpret the pinned checklist in the context of the actual control and project requirements.

## How It Works

1. Read the pinned local guidelines from the path below
2. Read the files identified by the request, owning package or relevant diff
3. Check against all rules in the pinned guidelines
4. Output findings in the terse `file:line` format

## Guidelines Source

Read the pinned local guidelines before each review:

```
references/web-interface-guidelines.md
```

Pinned upstream source: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/434b7f91364665f2f733b310ec54809bf8f37937/command.md

The local copy contains all the rules and output format instructions. Read it instead of fetching floating upstream rules.

## Usage

When a user provides a file or pattern argument:
1. Read the pinned local guidelines above
2. Read the specified files
3. Apply all rules from the pinned guidelines
4. Output findings using the format specified in the guidelines

If no files are specified, use the request's owning package or relevant diff to bound the review. Ask only when the target remains genuinely ambiguous; do not turn a clear read-only request into edits or application execution.
