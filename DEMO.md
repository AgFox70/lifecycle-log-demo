# Demo script (about 15 minutes)

The point: the system knows which signatures each record and document needs, and the CI enforces them.
Main starts empty (empty portal). Merging the good branches in order fills it. The `x` branches are blocked on purpose.

Two browsers: **Author** (AgFox70) opens PRs, **Approver** (authorStanleyCSV) approves. Reset first: `sh tools/reset_demo.sh`.

## How it works in one breath
Each record has its own states and approvals (`lifecycles.json`). An approval is a signature file such as
`signatures/R-21_Approve.CC-001.json`: a real SSH signature over the record hash, role and target state.
The workflow builds the PR description per record, verifies the files, and merges once a non-author approves last.
State is the last entry of the audit trail, written by CI after the merge.

## The good path (merge in this order: open a PR from each branch, approve as the other account)
Documents (SOP, WI, REC) only reach main approved, so they have no state to tick: the approvals table is there the moment the PR opens.
Only the stateful types (change control, incident, risk, deviation, CAPA, supplier) have tick-boxes. A new record starts at its first state with no click; ticking another box replaces the old one.

| Branch | Tick | Result |
|---|---|---|
| `s01-create-change-controls` | nothing (CC-001, CC-002 start at New) | portal gets 2 change controls |
| `s02-add-approved-documents` | nothing | SOP-014, WI-031, REC-052 arrive approved, each with its own approvals table, all signed |
| `s03-approve-changes` | CC-001, CC-002 Approved | R-23 signed |
| `s04-implement-change` | CC-001 Implemented | allowed because its documents are approved; R-21 signed |
| `s05-create-other-records` | nothing | incident, risk, deviation, CAPA, supplier appear |
| `s06-progress-records` | INC In Progress, SUP Under Evaluation, RSK Developing, DEV Develop | four records, one PR, one table each |
| `s07-close-change` | CC-001 Closed | R-21, Author and R-11 signed |
| `s08-revise-sop` | nothing | a revision of SOP-014 needs fresh signatures; the old ones show as stale until re-signed |

## The blocked variants (open the PR, show the table and the failing check, close it; do not merge)
- `s02x-no-signatures`: every row pending. Then sign live: `python3 tools/sign.py R-11 SOP-014 Approved`, push, watch the row turn signed.
- `s02x-partial-signatures`: R-11 missing for SOP-014 and WI-031.
- `s02x-wrong-signer`: the R-11 file on SOP-014 was signed by someone who does not hold R-11: invalid.
- `s02x-stale-signature`: WI-031 was edited after signing: stale.
- `s04x-implement-with-unapproved-docs`: CC-002 to Implemented while its attached SOP and WI have no signatures.
- `s06x-skip-a-stage`: tick RSK-001 Board straight from New: blocked, allowed next states listed.
- `s07x-close-without-quality`: closing CC-001 without the R-11 signature.
- `s08x-revise-sop-unsigned`: SOP-014 revised, old signatures stale.
- Approve a PR before signatures are in: nothing merges. Push after approving: the approval is stale and does not count.

## Extras
- Portal (local page): run `sh tools/portal.sh` after each merge; filter by type and state, expand a row for its audit trail (signers, PR approver, record hash), Pending PRs tab.
- Open a signature file: the hash, the statement and the signature block.
- Merge by hand with the green button: possible on a private free repo (no branch protection), and it writes no audit entry.
  Say so; the real setup makes the gate a required check.
