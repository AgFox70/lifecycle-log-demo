"""Build the demo branches. main is empty (an empty portal). The branches form a chain: merge the good ones
in order (s01, s02, s03, ...). The "x" branches are blocked on purpose; open them, show the block, close them.
Each branch is cut from the tip of the good branch before it, so its PR shows only its own changes."""
import subprocess, sys, pathlib
sys.path.insert(0, "tools")
import lc, content

def g(*a):
    r = subprocess.run(["git", *a], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"git {a}: {r.stderr}")
    return r.stdout

def new(rid, title, typ, change="", body=None, state=None):
    d = pathlib.Path(f"records/{typ}"); d.mkdir(parents=True, exist_ok=True)
    fm = f"---\nid: {rid}\ntitle: {title}\ntype: {typ}\nauthor: a.author\nowner: A. Author\n" + (f"change: {change}\n" if change else "") + "---\n"
    body = body or [f"## {x}\n\n_demo text_" for x in content.BODY[typ]]
    (d / f"{rid}.md").write_text(fm + f"\n# {title}\n\n" + "\n\n".join(body) + "\n")

def touch(rid, line="Updated for this change."):
    p = pathlib.Path(lc.find_record(rid)); s = p.read_text()
    if "## Change history" not in s: s += "\n## Change history\n"
    p.write_text(s.rstrip("\n") + f"\n\n- {line}\n")

def sign(role, rid, to, persona=None):
    if role == "Author": persona = "a.author"
    persona = persona or next(p for p, r in lc.ROLES["personas"].items() if role in r)
    lc.sign(persona, role, rid, to)

def branch(name, parent, msg, fn):
    g("checkout", "-q", "-B", name, parent); fn(); g("add", "-A"); g("commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    g("push", "-q", "--force", "origin", name); print("pushed", name)
    return name

def s01():
    for rid, t in (("CC-001", "Update retention wording"), ("CC-002", "Add supplier qualification step")): new(rid, t, "change-control")
    for rid, (t, typ, ch, _, body) in content.DOCS.items():
        if rid != "SOP-017": new(rid, t, typ, ch, body)

def s02_signed():
    for r in ("SOP-014", "WI-031", "REC-052"): touch(r, "Ready for approval.")
    for r, roles in (("SOP-014", ("Author", "R-08", "R-11")), ("WI-031", ("Author", "R-11")), ("REC-052", ("Author",))):
        for role in roles: sign(role, r, "Approved")

def s02_none():
    for r in ("SOP-014", "WI-031"): touch(r, "Ready for approval.")

def s02_partial():
    s02_none()
    for role in ("Author", "R-08"): sign(role, "SOP-014", "Approved")   # R-11 missing
    sign("Author", "WI-031", "Approved")                                # R-11 missing

def s02_wrong():
    s02_none()
    sign("Author", "SOP-014", "Approved"); sign("R-08", "SOP-014", "Approved")
    sign("R-11", "SOP-014", "Approved", persona="r21.signer")           # signed by someone who does not hold R-11
    sign("Author", "WI-031", "Approved"); sign("R-11", "WI-031", "Approved")

def s02_stale():
    s02_none()
    for role in ("Author", "R-08", "R-11"): sign(role, "SOP-014", "Approved")
    for role in ("Author", "R-11"): sign(role, "WI-031", "Approved")
    touch("WI-031", "Late edit after signing.")

def s03():
    for r in ("CC-001", "CC-002"): touch(r, "Approved to proceed."); sign("R-23", r, "Approved")

def s04():
    touch("CC-001", "Implemented."); sign("R-21", "CC-001", "Implemented")

def s04x():
    touch("CC-002", "Implemented."); sign("R-21", "CC-002", "Implemented")

def s05():
    for rid, t, ty in (("INC-001", "Portal unavailable for 20 minutes", "incident"), ("RSK-001", "Late signature capture", "risk"),
                       ("DEV-001", "Skipped second review on a form", "deviation"), ("CAPA-001", "Repeated late approvals", "capa"),
                       ("SUP-001", "Cloud hosting vendor", "supplier")): new(rid, t, ty)

def s06():
    for r in ("INC-001", "RSK-001", "DEV-001", "SUP-001"): touch(r)
    sign("R-21", "INC-001", "In Progress"); sign("R-21", "SUP-001", "Under Evaluation")

def s06x(): touch("RSK-001", "Board paper drafted.")

def s07():
    touch("CC-001", "All work verified.")
    for role in ("R-21", "Author", "R-11"): sign(role, "CC-001", "Closed")

def s07x():
    touch("CC-001", "All work verified.")
    for role in ("R-21", "Author"): sign(role, "CC-001", "Closed")

if __name__ == "__main__":
    t1 = branch("s01-create-records", "main", "Create two change controls and their documents (all Draft/New)", s01)
    for n, m, f in (("s02x-no-signatures", "Approve documents with no signatures", s02_none), ("s02x-partial-signatures", "Approve documents, R-11 missing", s02_partial),
                    ("s02x-wrong-signer", "Approve SOP with an R-11 signed by someone else", s02_wrong), ("s02x-stale-signature", "Edit after signing", s02_stale)):
        branch(n, t1, m, f)
    t2 = branch("s02-approve-documents", t1, "Approve SOP-014, WI-031 and REC-052 with all signatures", s02_signed)
    t3 = branch("s03-approve-changes", t2, "Approve both change controls (R-23)", s03)
    branch("s04x-implement-with-draft-docs", t3, "Implement CC-002 while its documents are Draft", s04x)
    t4 = branch("s04-implement-change", t3, "Implement CC-001 (documents Approved, R-21 signed)", s04)
    t5 = branch("s05-create-other-records", t4, "Create an incident, risk, deviation, CAPA and supplier evaluation", s05)
    branch("s06x-skip-a-stage", t5, "Risk jumps from New to Board", lambda: (touch("RSK-001"),))
    t6 = branch("s06-progress-records", t5, "Move four records on at once", s06)
    branch("s07x-close-without-quality", t6, "Close CC-001 without the R-11 signature", s07x)
    branch("s07-close-change", t6, "Close CC-001 with R-21, Author and R-11", s07)
    g("checkout", "-q", "main")
