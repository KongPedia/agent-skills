# Local incident packet
Question: Did the second reservation log mean inventory was deducted twice, and does this packet establish why production shipment dispatch skipped order A? This packet is a local reproduction; it has no production telemetry. No execution, internet access, dependency installation or code changes are needed for this question.

Write incident.json with these keys: `local_debits` (integer), `duplicate_debit` (boolean), `local_skip_reason` (string), `production_cause_established` (boolean), `evidence_paths` (list of repository paths supporting the answers), `next_evidence` (list of strings naming missing evidence to request). Use `cursor_after_order` for the skip reason if the cursor excludes A, otherwise `unknown`.

## Execution boundary
Do not run or import project/application code or tests. File inspection and tooling to format or write only the requested JSON artifact are allowed. Do not modify existing code/docs, access the network, install dependencies, or commit.
