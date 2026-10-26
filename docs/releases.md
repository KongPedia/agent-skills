# Releases, refresh and recovery

The first release is authorized for private [KongPedia/agent-skills](https://github.com/KongPedia/agent-skills) and
[KongPedia/project-blueprints](https://github.com/KongPedia/project-blueprints), with matching `v0.1.0` tags/releases.
Local/private indexes need no public-directory listing. Private distribution still must honor source licenses and
access rights; public visibility remains separately unauthorized and requires original-material licensing and scope review.
Record actual GitHub publication/CI results separately: authorization and this document are not completion evidence.

## One source, one release version

1. Edit canonical procedures/resources or roles, not generated `plugins/`. Preserve upstream revisions/licenses and
   separately record reviewed local changes. Keep stable plugin identities after first publication.
2. Update `catalog.json` version and matching `pyproject.toml`; run `uv lock` **without** `--upgrade` and review pins.
3. Rebuild plugins, run locked pytest and builder `--check`, then review artifact/provenance/license diffs. Release
   notes name changed triggers, compatibility, hook changes, observed checks and omitted host/session evidence.
4. With release authorization, commit and tag the reviewed commit as immutable `vX.Y.Z`. The private first release's
   authorized version is `v0.1.0`. Validation rejects a
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

For a Git-registered Codex index:

```bash
codex plugin marketplace upgrade konglabs-agent-skills
codex plugin list --json
```

For local Codex sources, rebuild reviewed artifacts/version, follow the selected-install/refresh flow and inspect
installed metadata; Git marketplace upgrade is not a local-checkout publication mechanism.

For Claude, refresh both the listing and each selected installed plugin, then reload/start a new session. These are
reference commands; Claude execution remains unverified here:

```bash
claude plugin marketplace update konglabs-agent-skills
claude plugin update common@konglabs-agent-skills
# Repeat the plugin update for the other selected installed bundles.
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

`.github/workflows/validate.yml` uses read-only permissions and immutable action SHAs. It runs locked tests, deterministic
artifact checks and tag/catalog/package/lock agreement; it does not publish, deploy, grant trust or contact hardware.
The optional cross-repository job requires `BLUEPRINTS_CONTRACT_REF` set to a reviewed blueprint commit after publication.
An unset variable skips that integration layer: it is **not a passing contract check**. Private sibling checkouts also
need separately provisioned read access; the default repository-scoped workflow token may not grant it. The job checks out the consumer
only in CI and invokes its small identity/dependency checker; no end-user clones or copied Markdown are involved.

Isolated local registration/flags-only and file-Git/cache tests do not establish private authentication, actual CI results, App/Claude discovery,
model adherence, hook trust or production safety. Those remain separately observed release acceptance layers.
