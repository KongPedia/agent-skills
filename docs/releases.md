# Releases, refresh and recovery

The first private release was published to [KongPedia/agent-skills](https://github.com/KongPedia/agent-skills) and
[KongPedia/project-blueprints](https://github.com/KongPedia/project-blueprints), with matching `v0.1.0` tags/releases.
Local/private indexes need no public-directory listing. Private distribution still must honor source licenses and
access rights; public visibility remains separately unauthorized and requires original-material licensing and scope review.
New commits, tags, pushes, releases and visibility changes require current task-specific authorization; historical
publication and this document grant none. Record actual GitHub publication/CI results separately.

## One source, one release version

1. Edit canonical procedures/resources or roles, not generated `plugins/`. Preserve upstream revisions/licenses and
   separately record reviewed local changes. Keep stable plugin identities after first publication.
2. Update `catalog.json` version and matching `pyproject.toml`; run `uv lock` **without** `--upgrade` and review pins.
3. Rebuild plugins, run locked pytest and builder `--check`, then review artifact/provenance/license diffs. Release
   notes name changed triggers, compatibility, hook changes, observed checks and omitted host/session evidence.
4. With release authorization, commit and tag the reviewed commit as immutable `vX.Y.Z`. The existing private first release
   uses `v0.1.0`; it does not authorize a future release. Validation rejects a
   tag that differs from the canonical catalog/package version. Do not move old release tags.
5. If an approved moving **`stable`** channel is maintained, promote only a validated release commit to it; `main` is
   development. Otherwise advance a registered immutable ref deliberately. Pushing a tag alone does not move the
   channel, retarget hosts, update installed plugins or reload sessions.

All bundle manifests use the one catalog version; Claude marketplace entries do not repeat it. There is no second
skill snapshot or release service in `project-blueprints`. Blueprint profile-to-plugin IDs form a public contract,
not a copy of the source inventory. Changes to that contract need coordinated consumer migration/review.

## Host updates

Projects normally emit activation flags only and use the index already registered on each host. A local index follows
its accessible checkout and reviewed generated artifacts; it has no imaginary Git channel. When using a Git source,
a reviewed moving `stable` channel can advance shared updates without editing every project selection. Immutable refs
are an explicit freeze. Neither source choice is a per-project installed-version lock when hosts share identity/cache.

### Moving channel versus pinned revision

A version change on `main` is not a broadcast to product repositories or developer machines. The provider must update
`catalog.json`, matching package/lock version and generated plugin manifests; editing skill text without a new manifest
version is not a reliable installed-payload update. An already enabled bundle keeps its stable identity across releases.

| Registered source ref | What a host refresh can receive |
| --- | --- |
| `main` | The reviewed current `main` commit, including a rebuilt `0.1.1` release |
| Team-maintained moving `stable` | `0.1.1` only after the team advances that channel |
| Immutable `v0.1.0` or commit | The same frozen payload; a new version elsewhere does not retarget it |

For a **new** host registration that deliberately follows `main`:

```bash
codex plugin marketplace add KongPedia/agent-skills --ref main
```

An existing same-name registration must be inspected first. Re-running an add or changing a project ref is not proof
that its cached Git source was retargeted. Deliberate channel changes are separate from routine refresh. Prefer an
actually maintained reviewed release channel when that is the team's policy; `stable` is not created automatically.

For a Git-registered Codex index:

```bash
codex plugin marketplace upgrade konglabs-agent-skills
codex plugin list --marketplace konglabs-agent-skills --json
# Verify installed versions, then start a fresh Codex session.
```

A controlled Codex **0.164.0** Git-source compatibility check observed an installed `common` payload change from
`0.1.0` to `0.1.1` during marketplace upgrade when following `main`; a registration pinned to `v0.1.0` remained frozen,
even after re-adding the plugin. This establishes that client/scenario, not universal automatic timing or other clients.
Inspect every selected installed version rather than treating a successful snapshot refresh as unconditional payload
proof. See [native marketplace commands](https://learn.chatgpt.com/docs/developer-commands#codex-plugin-marketplace).

Already-enabled product repositories need **no Copier update or new product commit** merely for shared skill text
changes when bundle identities/selection stay the same. Each developer/agent/CI host refreshes its own source and
installed payloads. Selection/routing changes and the first migration from customized local Markdown are separate
reviewed product changes; a host refresh never retires those local files. Shared provider releases also do not require
a template version bump merely because skill bodies changed.

For local Codex sources, rebuild reviewed artifacts/version, follow the selected-install/refresh flow and inspect
installed metadata; Git marketplace upgrade is not a local-checkout publication mechanism.

For Claude, refresh both the listing and each selected installed plugin, then reload/start a new session. These are
reference commands; Claude execution remains unverified here:

```bash
claude plugin marketplace update konglabs-agent-skills
claude plugin update common@konglabs-agent-skills --scope project
# Use the actual installation scope (project/user/local); repeat for other selected bundles.
claude plugin list --json
# Start a fresh session, or use /reload-plugins where supported.
```

Third-party auto-update stays off unless the user/team deliberately opts in. Inspect effective installed versions and
fresh-session discovery; configuration or a catalog listing is not model-invocation proof. Other developer/CI hosts
need their own refresh. Changed hook definitions still require separate trust; never overwrite that personal state.

## Recovery

For first-run `plugin X not found in marketplace konglabs-agent-skills`, use [source registration recovery](hosts.md#first-run-error-plugin-not-found).
Register the reviewed source once only if missing, then retry selected adds/Copier after inspecting the destination.
An existing same-name source must be reviewed, not silently replaced; stale Git caches are not fixed by changing URL/ref alone.

Prefer **fix-forward**: publish a new version restoring prior approved content, validate it and promote that release.
This changes the cache version without rewriting tags/history. Historical source downgrade is a separate tested host
operation, not a promised per-repository rollback. Do not edit caches or overwrite unrelated personal/project settings.
Existing sessions may retain old instructions until reloaded. Review local copied-skill customizations before any
manual migration from old draft templates; no automatic destructive retirement is provided.

## Validation workflow

`.github/workflows/validate.yml` limits its built-in token to read-only permissions and uses immutable action SHAs. It runs locked tests, deterministic
artifact checks and tag/catalog/package/lock agreement; it does not publish, deploy, grant trust or contact hardware.
The optional cross-repository job runs only on trusted pushes to the configured branches/release tags. An unset
`BLUEPRINTS_CONTRACT_REF` or any pull request (including forks) skips that layer: **not verified**, not a passing contract.
Ordinary repository validation still runs on pull requests. Do not change this to a privileged PR trigger to expose
credentials/private sibling contents to unreviewed PR code; fork workflows normally cannot receive these secrets.
See [GitHub's secret availability rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#using-secrets-in-a-workflow).

After private publication, an authorized maintainer configures these separately in each workflow repository:

| Workflow repository | Actions variable: reviewed full 40-hex sibling commit SHA | Actions secret |
| --- | --- | --- |
| `agent-skills` | `BLUEPRINTS_CONTRACT_REF` (`project-blueprints` commit) | `SHARED_REPOSITORY_READ_TOKEN`, authorized for `project-blueprints` |
| `project-blueprints` | `AGENT_SKILLS_CONTRACT_REF` (`agent-skills` commit) | `SHARED_REPOSITORY_READ_TOKEN`, authorized for `agent-skills` |

Use a [fine-grained, expiring token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
restricted to the named sibling with repository **Contents: read** permission;
the same secret name in each repository need not contain the same token. Provision the credential before setting
the ref; neither setup operation is performed by this workflow. Review the actual commit separately: CI enforces
40-hex syntax, not human review. Branch names, tags and short SHAs are rejected. The preflight fails with a named
configuration diagnostic before checkout if the ref is invalid or the secret is absent, without printing either value.

The [default `GITHUB_TOKEN` is limited to its workflow repository](https://docs.github.com/en/actions/concepts/security/github_token#about-the-github_token);
it is not a fallback for a private sibling. The explicit secret is supplied only to the isolated configuration
preflight and [private sibling checkout](https://github.com/actions/checkout#checkout-multiple-repos-private), not to
repository scripts or job-wide environment. Both checkouts disable credential persistence. The job then invokes
the small identity/dependency checker; no end-user clones or copied Markdown are involved. Only an observed hosted
run proves authentication and this integration layer; local YAML/shell checks do not.

Isolated local registration/flags-only and file-Git/cache tests do not establish private authentication, actual CI results, App/Claude discovery,
model adherence, hook trust or production safety. Those remain separately observed release acceptance layers.
