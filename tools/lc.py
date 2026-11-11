"""Shared helpers for the demo: config, record lookup, hashing, demo signatures (real SSH signatures)."""
import json, hashlib, pathlib, re, subprocess, tempfile, datetime, os, glob

CFG = json.load(open("lifecycles.json"))


def derive(t):
    """Each state lists the states it can be reached from (itself included if the record may be edited
    while it stays there) and the approvals needed to enter it. The rest is worked out from that."""
    defs, names = t["states"], list(t["states"])
    return {**t, "states": names, "defs": defs, "initial": names[0],
            "transitions": {s: [x for x in names if x != s and s in defs[x]["from"]] for s in names},
            "editable": [s for s in names if s in defs[s]["from"]],
            "approvals": {s: d["approvals"] for s, d in defs.items() if d["approvals"]}}


TYPES = {k: derive(v) for k, v in CFG["types"].items()}
ROLES = json.load(open("roles.json"))
NS = "lifecycle-demo"
PAYLOAD_KEYS = ["record", "role", "meaning", "to_state", "record_sha256", "signer", "signed_at", "statement"]
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def front(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)) if m else {}


def find_record(rid):
    hits = glob.glob(f"records/*/{rid}.md")
    return hits[0] if hits else None


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(d):
    return json.dumps({k: d[k] for k in PAYLOAD_KEYS}, sort_keys=True, separators=(",", ":"))


def attached(cid):
    """Records whose front matter says change: <cid>."""
    return sorted(pathlib.Path(p).stem for p in glob.glob("records/*/*.md") if front(open(p).read()).get("change") == cid)


def sig_path(role, rid):
    return f"signatures/{role}_Approve.{rid}.json"


def sign(persona, role, rid, to_state, key_dir="demo-keys"):
    rec = find_record(rid)
    d = {"record": rid, "role": role, "meaning": "approve", "to_state": to_state, "record_sha256": sha256_file(rec),
         "signer": persona, "signed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "statement": f"I approve {rid} moving to {to_state} in my role {role}."}
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "payload"
        p.write_text(canonical(d))
        k = pathlib.Path(td) / "key"
        k.write_bytes(pathlib.Path(f"{key_dir}/{persona}").read_bytes())
        k.chmod(0o600)
        r = subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(k), "-n", NS, str(p)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("signing failed: " + r.stderr)
        d["signature"] = (pathlib.Path(str(p) + ".sig")).read_text()
    out = {"schema": "lifecycle-demo/signature/1", **d}
    pathlib.Path("signatures").mkdir(exist_ok=True)
    pathlib.Path(sig_path(role, rid)).write_text(json.dumps(out, indent=2) + "\n")
    return sig_path(role, rid)


def verify(path, rid, role, to_state, author):
    """Return (status, detail, signer): status is signed | pending | stale | invalid."""
    p = pathlib.Path(path)
    if not p.exists():
        return "pending", "", None
    try:
        d = json.load(open(p))
        signer = d["signer"]
    except Exception:
        return "invalid", "unreadable signature file", None
    if d.get("record") != rid or d.get("role") != role:
        return "invalid", "file does not match its name", signer
    if d.get("to_state") != to_state:
        return "stale", f"signed for {d.get('to_state')}, not {to_state}", signer
    if d.get("record_sha256") != sha256_file(find_record(rid)):
        return "stale", "record changed after signing", signer
    with tempfile.TemporaryDirectory() as td:
        sig = pathlib.Path(td) / "s.sig"
        sig.write_text(d.get("signature", ""))
        r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", "demo-keys/allowed_signers", "-I", signer, "-n", NS, "-s", str(sig)],
                           input=canonical(d), capture_output=True, text=True)
    if r.returncode:
        return "invalid", "signature does not verify", signer
    held = ROLES["personas"].get(signer, [])
    if role == "Author":
        if signer != author:
            return "invalid", f"{signer} is not the record author ({author})", signer
    elif role not in held:
        return "invalid", f"{signer} does not hold {role}", signer
    return "signed", "", signer
