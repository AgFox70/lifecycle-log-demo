# Demo script (about 15 minutes)

The point: the system knows which signatures each record and document needs, and the CI enforces them.
Main starts empty (empty portal). Merging the good branches in order fills it. The `x` branches are blocked on purpose.

Two browsers: **Author** (AgFox70) opens PRs, **Approver** (authorStanleyCSV) approves. Reset first: `sh tools/reset_demo.sh`.

## How it works in one breath
Each record has its own states and approvals (`lifecycles.json`). An approval is a signature file such as
`signatures/R-21_Approve.CC-001.json`: a real SSH signature over the record hash, role and target state.
The workflow builds the PR description per record, verifies the files, and merges once a non-author approves last.
State is the last entry of the audit trail, written by CI after the merge.

## The good path (merge in this order; open a PR from each branch, tick the states, approve)
| Branch | Tick | Result |
|---|---|---|
| `s01-create-records` | CC-001, CC-002 New; documents Draft | no signatures needed; portal fills with 2 change controls and 7 documents |
| `s02-approve-documents` | SOP-014, WI-031, REC-052 Approved | tables show Author, R-08, R-11 signed; merge on approval |
| `s03-approve-changes` | CC-001, CC-002 Approved | R-23 signed |
| `s04-implement-change` | CC-001 Implemented | allowed because its documents are Approved; R-21 signed |
| `s05-create-other-records` | INC, RSK, DEV, CAPA, SUP at their first state | other portal tabs fill |
| `s06-progress-records` | INC In Progress, SUP Under Evaluation, RSK Developing, DEV Develop | four records, one PR, each with its own table |
| `s07-close-change` | CC-001 Closed | R-21, Author and R-11 signed |

## The blocked variants (open the PR, show the table and the failing check, close it; do not merge)
Open each from the point after the good branch it is cut from has merged (or just open it to show the table).
- `s02x-no-signatures`: every row pending. Then sign live: `python3 tools/sign.py R-11 SOP-014 Approved`, push, watch the row turn signed.
- `s02x-partial-signatures`: R-11 missing for SOP-014 and WI-031. Waiting for signatures.
- `s02x-wrong-signer`: the R-11 file on SOP-014 was signed by someone who does not hold R-11: invalid.
- `s02x-stale-signature`: WI-031 was edited after signing: stale.
- `s04x-implement-with-draft-docs`: CC-002 to Implemented while its SOP and WI are Draft: blocked.
- `s06x-skip-a-stage`: tick RSK-001 Board straight from New: blocked, with the allowed next states listed.
- `s07x-close-without-quality`: closing CC-001 without the R-11 signature: waiting.
- Approve a PR before signatures are in: nothing merges. Push after approving: the approval is stale and does not count.

## Extras
- Portal (local page): run `sh tools/portal.sh` after each merge; filter by type and state, expand a row for its audit trail (signers, PR approver, record hash), Pending PRs tab.
- Open a signature file: the hash, the statement and the signature block.
- Merge by hand with the green button: possible on a private free repo (no branch protection), and it writes no audit entry.
  Say so; the real setup makes the gate a required check.
