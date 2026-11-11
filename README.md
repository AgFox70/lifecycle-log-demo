# lifecycle-log-demo

Throwaway demo of a lifecycle-aware pull request. Fictional company and records.
Walk-through: `DEMO.md`.

- `lifecycles.json`: states, allowed moves and required approvals per record type (CC, INC, RSK, DEV, CAPA, SUP, SOP, WI, REC)
- `records/<type>/<ID>.md` with `<ID>.audit.json` beside it (state = last audit entry, written by CI). Documents point at their change control with `change:`
- `signatures/<ROLE>_Approve.<ID>.json`: demo approvals, real SSH signatures; `tools/sign.py` writes them; `demo-keys/` holds throwaway keys
- `tools/lifecycle_check.py`: the gate; builds the PR description per record, verifies signatures, merges, writes the audit trail
- `tools/portal.sh`: pull main, rebuild and open the local portal (`site/index.html`); `tools/build_portal.py` builds it; `tools/make_scenarios.py` rebuilds the `scn-*` branches; `tools/reset_demo.sh` resets main

## Lifecycle log

Live state of every record, rebuilt by CI after each merge (the same data as the portal).

<!-- LOG:START -->
_Updated 2026-11-11 11:04 UTC from the audit trail. 7 records._

### Change Control (2)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| CC-001 | Update retention wording | **Implemented** | 2026-11-11T11:04Z (PR #12) | R-21:r21.signer |
| CC-002 | Add supplier qualification step | **Approved** | 2026-11-11T10:55Z (PR #10) | R-23:r23.signer |

### Incident (1)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| INC-001 | Portal unavailable for 20 minutes | **New** | 2026-11-11T11:04Z (PR #12) | - |

### Risk (1)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| RSK-001 | Late signature capture | **New** | 2026-11-11T11:04Z (PR #12) | - |

### Deviation (1)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| DEV-001 | Skipped second review on a form | **New** | 2026-11-11T11:04Z (PR #12) | - |

### CAPA (1)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| CAPA-001 | Repeated late approvals | **Detection** | 2026-11-11T11:04Z (PR #12) | - |

### Supplier Evaluation (1)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| SUP-001 | Cloud hosting vendor | **New** | 2026-11-11T11:04Z (PR #12) | - |

<!-- LOG:END -->
