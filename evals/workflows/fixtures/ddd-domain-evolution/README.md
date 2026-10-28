# Product change request: "suspend this member's account"
An organization administrator wants to temporarily prevent one person from opening only this organization's workspace. The person should still be able to sign in and use their other organizations. Existing removal currently revokes membership; product has not decided whether a temporary restriction preserves the membership's active/removed lifecycle or adds a new membership state. Reinstatement, who may impose the restriction, and behavior of already-issued workspace sessions have not been decided. Existing code only checks access at can_open; do not claim running sessions are invalidated.

Prepare a decision proposal only. Read the local code, glossaries and existing accepted decision; distinguish overloaded existing terms from the new requested capability. Compare at least two genuinely different models, recommend one with trade-offs, and list decisions still needed. Do not implement a model or mark a decision accepted. Do not edit existing code, glossaries or ADRs. Avoid speculative service splits; no network, dependency installation, project/application code execution or commits. Shell file reads are allowed.

Write only proposal.json with this public schema (all keys required):
```
{
  "status": "proposed",
  "facts": {
    "login_context": "<context directory name>",
    "membership_context": "<context directory name>",
    "global_suspension_scope": "<all_workspaces or one_workspace>",
    "membership_removal_scope": "<all_workspaces or one_workspace>",
    "workspace_temporary_suspension_exists": false,
    "running_session_revocation_proven": false
  },
  "existing_terms": [
    {"context": "<context directory name>", "term": "Account or Member", "meaning": "<source-backed existing meaning>"}
  ],
  "evidence": [{"path": "<existing relative source path>", "supports": "<fact/meaning supported>"}],
  "proposal": {"capability": "<proposed term/behavior>", "owner": "<recommended responsibility owner>", "recommendation": "<recommended model and why>"},
  "alternatives": [{"model": "<distinct model>", "benefit": "<real benefit>", "cost": "<real cost>"}],
  "open_questions": ["<unresolved business decision>"],
  "implementation_changed": false,
  "accepted_decisions_changed": false
}
```
Describe both Account and Member in each existing context (four existing_terms entries). Cite existing files for the identity/member lifecycle facts and overloaded meanings. At least two alternatives and two open questions are required. Text fields must be substantive, not empty placeholders. Names, new capability ownership and recommended model are proposals: no one specific naming scheme or class hierarchy is prescribed. Correctness of the recommendation, evidence fit, trade-offs and uncertainty will be reviewed semantically; schema compliance alone is not design quality.

## Execution boundary
Do not run or import project/application code or tests. File inspection and tooling to format or write only the requested JSON artifact are allowed. Do not modify existing code/docs, access the network, install dependencies, or commit.
