# Doc Coverage Checklist

Use within the requested topic or diff. A full inventory requires a comprehensive audit request; the current branch
alone does not determine scope.

## Inventory and evidence

- Record the current branch, inspected revision, local changes, file path and relevant symbol or setting.
- Check public interfaces, configuration, environment variables, commands, defaults, errors and supported behavior.
- For agent guidance, inspect `AGENTS.md`, `.agents/` workflow/role/skill entrypoints and their actual references.
- Distinguish implemented, proposed, historical, software-tested, deployed and physically validated claims.

## Doc-first pass

- Review relevant `docs/` human operations pages and `.agents/` agent procedures in their existing language.
- Look for missing options, stale paths, incorrect defaults and duplicated canonical rules.
- Preserve unique approval, safety, rollback and validation instructions when consolidating pages.

## Code-first pass

- Map each supported feature or workflow to the closest existing page and actual index/navigation.
- Prefer focused updates and cross-links over new duplicate pages.
- Identify the real source of generated content; do not assume SDK, MkDocs or OpenAI-specific paths or tools.

## Patch and verification

- Edit only the authorized scope; update affected indexes and cross-links after moves or renames.
- For branch-scoped requests only, compare against the intended base without switching branches.
- Use the one-off metadata/reference/hash validation in `.agents/README.md`, parse changed configuration and review
  references plus `git diff --check`; do not add a persistent validator or test harness.
- Keep prose verification static: no application tests/builds, services, CI, deployment or hardware.
- Report check failures and omitted proof; static checks do not establish discovery or model adherence.
