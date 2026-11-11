"""Demo signing: python3 tools/sign.py <ROLE> <RECORD-ID> <TO-STATE> [--as persona]
Writes signatures/<ROLE>_Approve.<RECORD-ID>.json, a real SSH signature over the record's hash, the target
state and the role. Commit and push it to the PR branch."""
import sys, json
sys.path.insert(0, "tools")
import lc

a = sys.argv[1:]
persona = a[a.index("--as") + 1] if "--as" in a else None
role, rid, to = a[0], a[1], a[2]
if role == "Author":
    persona = persona or lc.front(open(lc.find_record(rid)).read()).get("author")
else:
    persona = persona or next(p for p, r in lc.ROLES["personas"].items() if role in r)
print("wrote", lc.sign(persona, role, rid, to), "as", persona)
