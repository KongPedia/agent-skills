# Local, private and shared plugin sources

A marketplace is a JSON index used by the host to resolve plugin identities. It is **not** a requirement to publish to
OpenAI's public directory or make this Git repository public. This checkout already includes both native indexes.

## First-run error: plugin not found

For `plugin X not found in marketplace konglabs-agent-skills`, check that the reviewed source has been registered.
If it has not, register it **once** on the host:

```bash
codex plugin marketplace add /path/to/agent-skills
```

Or, from the reviewed `agent-skills` checkout:

```bash
codex plugin marketplace add .
```

Then retry the selected plugin adds or Copier after inspecting its destination. If the marketplace name is already
registered, inspect source/revision/access instead of silently retargeting it. A wrong or stale same-name Git cache can
produce this symptom too; URL/ref changes alone do not prove the source used. Do not auto-register a replacement,
delete host caches or overwrite unrelated plugins to hide the failure.

Claude users register their reviewed source separately with `claude plugin marketplace add /path/to/agent-skills`.
Local delivery needs no remote. Keep the source checkout available; every developer/CI host needs its own access,
registration and refresh. Machine paths, caches, credentials and trust records do not belong in generated products.

## Native Copier generation

The existing published sources are [agent-skills](https://github.com/KongPedia/agent-skills) and
[project-blueprints](https://github.com/KongPedia/project-blueprints), with matching first-release `v0.1.0` tags/releases.
With Codex available, this marketplace registered and the project repository answer left empty:

```bash
uvx copier copy --trust https://github.com/KongPedia/project-blueprints.git ./my-project
```

Native questions select the profiles and the copy-only task runs their `codex plugin add` union. Review the source/ref
before `--trust`; it authorizes template task execution, not Codex workspace or hook trust. There is no custom creation
CLI, installation-confirmation wrapper or strict existing-target guard. Choose a new destination and inspect any
partial output before retrying; native Copier can clean up a newly created target after failure.

For Claude-only use, an unprovisioned host or scaffold review, use `copier copy --skip-tasks` instead. Generated
`.agents/plugin-setup.md` provides the selected manual recovery/Claude commands. For general Python:

```bash
# Codex manual recovery:
codex plugin add common@konglabs-agent-skills
codex plugin add python@konglabs-agent-skills
# Claude alternative:
claude plugin install common@konglabs-agent-skills --scope project
claude plugin install python@konglabs-agent-skills --scope project
```

The copy task does not register/retarget this index, install Claude/product dependencies, initialize Git or approve
trust. Missing Codex, source access or an add error stops the chain; prior successful installations are not rolled back.
Guidance adoption and updates do not install plugins. Copier 9.19.1 updates can still require `--trust` for prior task
metadata even with `--skip-tasks`; this native authorization does not change agent-host trust.

## Private Git source

For a new registration using the private first release instead of the local checkout:

```bash
codex plugin marketplace add KongPedia/agent-skills --ref v0.1.0
claude plugin marketplace add 'KongPedia/agent-skills#v0.1.0'
```

This is a historical first-release pin, not an instruction to install the current working tree. A frozen
`v0.1.0` does not follow later skill or layout changes. To inspect pending local changes, use the reviewed local
checkout described above; do not assume a new version in `catalog.json` has already been committed or published
as a Git tag. Existing same-name registrations still require source/cache inspection before any deliberate change.

Do not run this as an automatic replacement for an existing same-name registration. Private Git credentials/access
use normal host/Git mechanisms; the URLs do not grant access or prove a successful fetch, and credentials do not belong
in template answers. A project's advanced
nonempty `agent_skills_repository` is supported for render-only/manual review with `--skip-tasks`; the automatic copy
task rejects it before any add. It does not apply source overrides, retarget registration or fall back to copied skills.

Codex can reuse an existing same-name cached Git marketplace even when a different source/ref is passed through
configuration or CLI overrides. Those values do not prove the actual fetched source or installed bytes. Deliberately
register/refresh and inspect source/cache identity before manual installation; registration/refresh is host-owned, not
a Copier repair task. Automatic installation uses the already established host source with the project repository
left empty. `stable` is a reviewed moving channel only when maintained, not an independently verified payload lock.
Neither local nor private Git delivery requires public visibility or a directory submission. Actual release, private
authentication and hosted CI results require their own evidence; these commands do not certify App/Claude discovery.

## Ready plugins, not install-time builds

The marketplace selects an existing `plugins/<bundle>` directory. Its canonical `skills/` and prepared metadata,
licenses and local resources are Git-managed ready-to-install content. `codex plugin add` installs that package;
it does not run `scripts/build_plugins.py`, render Copier templates or install product dependencies.
Maintainers prepare and check changed metadata/resources before distribution. Consumers do not need the provider's
maintainer environment. UI UX Pro Max's optional local search has its own existing-Python requirement.

A host cache is an installed copy, not another editable source of truth. Update the provider's recorded canonical
file, distribute the reviewed version, then refresh and inspect the host installation separately.

## Activation is not trust or adherence

Generated settings make explicit true/false decisions for every known team plugin. A trusted Codex project can override
host defaults; untrusted projects can ignore those overrides. Preserve unrelated user plugins and managed policy.
A monorepo selects a union; project routing chooses the actual owning package's procedures. This is not a model sandbox.
Native installation is host-scoped and globally enables selected identities; project flags apply only after project
trust. Repeated adds use native cache/installation behavior, not independent per-project versions. Shared releases still
refresh through the host, not through Copier update.

Flags alone are not installation/discovery proof. Host startup synchronization can be asynchronous, and refresh can
fetch/install configured disabled plugins too: false controls loading, not a no-download guarantee. Inspect effective
installed versions and start a fresh session before relying on discovery. App/CLI/IDE support differs.

## Optional hooks and native agents

`session-guidance` is separately opt-in and off by default. Its SessionStart hook is POSIX printf-only: no scan, network,
tests, permission mutation, services or hardware. Installation/enablement does not grant hook trust; review definitions
through `/hooks` where supported and respect hook-disable policy. Never override personal trust records.

Each package has portable root `plugin.json` for Codex and `.claude-plugin/plugin.json` for Claude. `.codex-plugin` is
an optional compatibility location, not a consumer directory for selected skills.
Common's Claude-native `agents/*.md` derive from canonical `plugins/common/exports/codex/agents/*.toml`.
Those TOMLs are optional explicit provisioning artifacts: Codex 0.160.0 and the inspected bundled 0.162.0-alpha.17.2 do not load agents from plugins.
Use built-in Codex agents by default; custom roles require separate native `.codex/agents` provisioning. A skill's
`agents/openai.yaml` is interface metadata, not custom-agent registration.

## Google Antigravity

Skill-bearing bundles include a generated `.antigravity-plugin/plugin.json`, using the existing bundle ID and catalog
version. They reuse the same `skills/`, resources and license evidence; do not create a second `.antigravity/` tree.
Antigravity supports this multi-provider manifest location with components at the plugin root.
See Google's [plugin authoring guide](https://antigravity.google/docs/build-plugins/).

### Local installation

Use a reviewed local checkout and select each bundle explicitly. `requires` and `DEPENDENCIES.md` describe composition,
not automatic dependency installation. The Codex/Claude marketplace indexes do not register an Antigravity marketplace.
This repository does not document unverified GitHub monorepo-subdirectory installation syntax.

The following commands follow Google's [plugin CLI documentation](https://antigravity.google/docs/plugins).
They have not been executed against a working Antigravity CLI for this change; install the official CLI separately,
review its version/help, and run them from this checkout only after reviewing the package:

```bash
agy plugin validate --json ./plugins/python
agy plugin install ./plugins/python
agy plugin list --json
```

Inspect every validation finding before installation. Multi-provider packages can warn about a shadowed root
`plugin.json` or other tools' files. Do not suppress unknown warnings; `--strict` treats all warnings as errors.
Native CLI validation and installation remain separate from fresh-session discovery and invocation.
For maintainer installation tests, use disposable host configuration rather than personal settings/authentication.

Google documents project plugins at `.agents/plugins/<plugin>/` and global plugins at
`~/.gemini/config/plugins/<plugin>/`. Project-only skills use `.agents/skills/<skill>/SKILL.md`, and global skills use
`~/.gemini/config/skills/<skill>/SKILL.md`. Use `.agents/` for new projects, not legacy `.agent/`.
Project provisioning remains owned by the consuming project or `project-blueprints`; no Copier integration is added here.

### Common roles and the skills-only alternative

**Do not treat installing Common as skills-only.** Its `agents/*.md` are generated Claude adapters, and Antigravity's
default plugin discovery can expose those files as custom agents. Their Antigravity behavior and tool/permission
semantics have not been validated. Until reviewed and tested, prefer a skills discovery manifest for Common rather
than installing its whole plugin. Do not infer safety restrictions from the role prose alone.

Google's [customization discovery guide](https://antigravity.google/docs/customization-discovery/) supports a personal
`~/.gemini/config/skills.json` pointing to existing skill directories. This documentation-only example loads Common
skills without selecting its plugin-level agents; replace the absolute path and merge with any existing entries:

```json
{
  "entries": [
    {
      "path": "/absolute/path/to/agent-skills/plugins/common/skills"
    }
  ]
}
```

Keep the reviewed checkout available. This route follows its current files, not a separately installed version;
review changes before refreshing. Include other required bundles explicitly, preserve existing personal configuration,
and inspect Customizations or the CLI skill list in a fresh session to verify loaded names and paths. Then invoke a
selected skill and verify access to its bundled references/scripts. No such Antigravity session test is claimed here.

### Unsupported components and release limits

- `session-guidance` intentionally has no Antigravity manifest: its existing `hooks/hooks.json` and printf-only advisory
  are not an Antigravity hook port. No Antigravity root `hooks.json` or permission changes are added.
- No Antigravity-specific role adapter, MCP configuration, marketplace submission or host installation is added.
- Shared skill prose can reference host-specific tools or project paths. Packaging checks do not prove those tools
  exist or that an Antigravity agent follows the procedure; report missing capabilities instead of inventing substitutes.
- Replacing or refreshing an installed bundle is a host operation. Inspect the native CLI's supported update behavior,
  source/version and installed bytes; do not edit its cache or assume a provider checkout change updated an installation.

These are local packaging instructions, not a published Antigravity Marketplace listing or a release authorization.

## References and limits

- [OpenAI local/private catalogs, packaging and registration](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work)
- [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)
- [Claude commands and local/private sources](https://code.claude.com/docs/en/plugins/cli-reference)
- [Releases, refresh and recovery](releases.md)

Isolated native CLI installation/configuration checks are not actual App/Claude discovery, model invocation/adherence,
host hook execution, hosted CI, deployment or physical validation. No personal host configuration was changed.
