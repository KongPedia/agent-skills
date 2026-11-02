# Frontend design, review and interaction guidance

Use this guide to select existing `react-ui` skills, not as a required workflow or a replacement for a project's
design system, accessibility requirements, package instructions or the user's request. The bundle contains reviewed
upstream skill material; its source, adaptations, licenses and pinned revisions remain in
[`source/skill-sources.json`](../source/skill-sources.json).

## Choose by the requested work

| Request | Skill | Boundary |
| --- | --- | --- |
| Create or substantially reshape a UI; avoid a generic look | [`frontend-design`](../source/skills/frontend-design/SKILL.md) | Start from the actual brief, audience and existing visual language. Upstream's fictional client scenario is not evidence about the current user. |
| Audit, critique, polish or harden a specific existing UI | [`impeccable`](../source/skills/impeccable/SKILL.md) | Select the relevant instruction-only reference; preserve existing design and behavior unless redesign is requested. The upstream CLI, detector, hooks and browser tooling are not included. |
| Review a target for interface and accessibility issues | [`web-design-guidelines`](../source/skills/web-design-guidelines/SKILL.md) | Use the pinned local checklist and report findings with locations and evidence. Interpret rules against the actual control and project. |
| Examine React/Next.js rendering, data or bundle performance | [`vercel-react-best-practices`](../source/skills/vercel-react-best-practices/SKILL.md) | Apply relevant guidance to the installed framework and measured problem; a rule or build alone does not establish a performance gain. |
| Change a React component's composition, state ownership or reusable API | [`vercel-composition-patterns`](../source/skills/vercel-composition-patterns/SKILL.md) | Use composition where the existing component and callers benefit; do not add compound components or context by default. |

UI-specific anti-slop guidance is already present in `frontend-design` and `impeccable`; neither provides an
automatic detector in this bundle. Treat visual tropes as prompts for review, not a universal ban on fonts,
colors, cards, layouts or motion. Avoid inventing product facts or replacing a requested or established design
merely because it resembles a template. There is no separately owned `ai-slop` skill in this catalog.

These skill identities make selection possible; they do not prove a host discovered or invoked them, that an agent
followed them, or that a UI improved. Do not install or enable additional tools merely to use the guidance.

## Evidence for the changed surface

- **Source or supplied image only:** inspect the relevant implementation or provided design and report the findings
  at that layer. An image cannot establish clickable area, keyboard behavior, accessibility-tree output or runtime
  state; source alone does not establish rendered layout.
- **Visual review, when in scope and execution is authorized:** inspect the actual viewport and relevant loading,
  empty, error, populated and responsive states. Record the target, viewport and what was observed; a screenshot
  from another state or viewport is not proof of this one.
- **Interaction, when in scope and execution is authorized:** use pointer and keyboard to verify the requested
  action, including focus visibility, activation and the intended clickable area. A native button or link already
  provides keyboard behavior; do not add redundant key handlers solely to satisfy a static pattern.
- **Accessibility:** assess applicable requirements, states and exceptions for the actual interface. Useful W3C
  references include [keyboard](https://www.w3.org/TR/WCAG22/#keyboard), [focus visible](https://www.w3.org/TR/WCAG22/#focus-visible),
  [text contrast](https://www.w3.org/TR/WCAG22/#contrast-minimum) and [target size](https://www.w3.org/TR/WCAG22/#target-size-minimum).
  A checklist, screenshot or automated scan alone is not a WCAG conformance certification or proof of usability.

Read-only review does not authorize edits. When execution is excluded, use supplied evidence and state what remains
unverified; do not require a browser, service, `DESIGN.md`, MCP server or dependency installation. If execution is
allowed, use the project's existing tools and do not treat guidance as permission to deploy or access hardware.

## Upstream references

These links document the pinned origins, not additional installed components or a claim of measured improvement:

- [Anthropic frontend-design at the pinned revision](https://raw.githubusercontent.com/anthropics/claude-plugins-official/465f09344424225c25d438f2e052732c3d688d2f/plugins/frontend-design/skills/frontend-design/SKILL.md)
- [Impeccable at the pinned revision](https://github.com/pbakaus/impeccable/tree/936867543ac2576920d663cc9803597f6044f3ac) — this repository packages only the selected instruction-only adaptation described above.
- [Vercel agent skills at the pinned revision](https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278)
- [Vercel Web Interface Guidelines at the pinned revision](https://github.com/vercel-labs/web-interface-guidelines/blob/434b7f91364665f2f733b310ec54809bf8f37937/command.md)
