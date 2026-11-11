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
_Updated 2026-11-11 10:41 UTC from the audit trail. 2 records._

### Change Control (2)

| ID | Title | State | Last change | Signatures |
|---|---|---|---|---|
| CC-001 | Update retention wording | **New** | 2026-11-11T09:08Z (PR #6) | - |
| CC-002 | Add supplier qualification step | **New** | 2026-11-11T09:08Z (PR #6) | - |

### Incident (0)

_None yet._

### Risk (0)

_None yet._

### Deviation (0)

_None yet._

### CAPA (0)

_None yet._

### Supplier Evaluation (0)

_None yet._

<!-- LOG:END -->
