# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, the invocation choice, and router skills). Everything else about writing it is the universal reference in `SKILL.md`.

## Invocation

A skill description is a routing pointer: state its capability and actual trigger branches.
Discoverable skills can also be requested explicitly. Descriptions and an on-disk entrypoint
make selection possible, but do not prove discovery, loading, understanding or adherence.

Invocation controls are harness-specific. The upstream Claude-oriented
`disable-model-invocation` setting and zero-context claims are not imported as Codex
metadata. Use the exact local entrypoint in the task catalog and preserve the existing
invocation policy. Do not introduce plugin/router metadata or change automatic selection
without a separately scoped need and verified target-harness support.

Shared reference can live in a plain linked file. Keep the pointer's condition precise,
and load that reference only on the relevant branch. This trades a small routing pointer
for less always-loaded content; it does not promise zero context cost.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): consider a separate discoverable skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.

## Router skills

When a real catalog becomes hard to navigate, improve its task-to-entrypoint pointers
first. This repository uses the existing [.agents workflow](../../README.md#required-skill-selection-and-evidence);
this reference does not require another router skill or a plugin bundle. Create a new
router only if the requested scope and observed navigation problem justify it.
