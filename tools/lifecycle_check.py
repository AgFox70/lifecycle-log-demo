"""Demo lifecycle gate. One PR, many records and documents, no families.

1. Every changed record under records/ gets its own section in the PR description: a tick-list of its states
   and an approvals table for the state that is ticked.
2. Each move is checked against lifecycles.json (current state comes from the last audit entry on the base branch).
3. Approvals are signature files such as signatures/R-21_Approve.CC-001.json (real SSH signatures over the
   record hash, role and target state). They are verified here. The PR author's own role is "Author".
4. A change control cannot move to Implemented while its attached documents are not Approved.
5. When rules pass, every signature verifies and a non-author has approved the PR at the head commit,
   the workflow merges the PR and writes the audit entries to main.
"""
import json, os, re, subprocess, sys, pathlib, tempfile, datetime
sys.path.insert(0, "tools")
import lc

T, ROLES = lc.TYPES, lc.ROLES
MARK = "<!-- lifecycle-status -->"
GIT_ID = ["-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]
ICON = {"signed": "✅ signed", "pending": "⏳ pending", "stale": "⚠️ stale", "invalid": "❌ invalid"}


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def rtype(rid):
    p = lc.find_record(rid)
    return p.split("/")[1] if p else None


def parse_body(body):
    ticks = {}
    for m in re.finditer(r"<!--\s*record:\s*([\w-]+)\s*-->(.*?)(?=<!--\s*record:|## Notes for approvers|\Z)", body or "", re.S):
        t = rtype(m.group(1))
        if t:
            got = [x for x in re.findall(r"^- \[[xX]\] (.+?)(?: \(current\))?\s*$", m.group(2), re.M) if x in T[t]["states"]]
            prev = re.search(r"<!-- sel: (.*?) -->", m.group(2))
            if len(got) > 1:  # a new box was ticked on top of the old one: keep the new one
                got = [x for x in got if not prev or x != prev.group(1)][-1:]
            ticks[m.group(1)] = got
    notes = ""
    if "## Notes for approvers" in (body or ""):
        notes = body.split("## Notes for approvers", 1)[1].strip()
    elif body and "<!-- default-form -->" not in body and "<!-- lifecycle-form -->" not in body and not ticks:
        notes = "Original description:\n\n" + body.strip()
    return ticks, notes


def state_at(base, rid):
    p = lc.find_record(rid)
    r = sh("git", "show", f"origin/{base}:{p[:-3]}.audit.json") if p else None
    return json.loads(r.stdout)["entries"][-1]["record_state"] if r is not None and r.returncode == 0 else None


def section(rid, ticks, cur, info, extra=""):
    fm = lc.front(open(lc.find_record(rid)).read())
    t = T[rtype(rid)]
    sel = ticks.get(rid, [])
    if t.get("implied"):  # documents: only approved versions reach main, so no state to pick
        out = [f"<!-- record: {rid} -->\n### {rid}: {fm.get('title','')}\n",
               f"{t['name']}. " + ("New document." if cur is None else "Revision of the approved document.") + (f" Attached to **{fm['change']}**." if fm.get("change") else "") + "\n"]
        rows = info.get(rid, [])
        tbl = "\n".join(f"| {role} | {ICON[st]}{(' by ' + who) if who and st == 'signed' else ''}{(': ' + why) if why else ''} |" for role, st, who, why in rows)
        out.append(f"The following approvals are required for this document:\n\n| Approvals | Status |\n|:---:|:---|\n{tbl}\n")
        out.append(f"Sign with `python3 tools/sign.py <role> {rid} {t['implied']}`, then commit and push the file in `signatures/`.\n")
        return "\n".join(out) + extra
    boxes = "\n".join(f"- [{'x' if s in sel else ' '}] {s}" + (" (current)" if s == cur else "") for s in t["states"])
    out = [f"<!-- record: {rid} -->\n### {rid}: {fm.get('title','')}\n",
           f"{t['name']}. Current state: **{cur or 'not yet created'}**." + (f" Attached to **{fm['change']}**." if fm.get("change") else "") + "\n",
           f"Please select the required state for this {t['name']} (tick a different box to change it):\n\n{boxes}\n" + (f"<!-- sel: {sel[0]} -->\n" if len(sel) == 1 else "")]
    if len(sel) == 1 and rid in info:
        to, rows = sel[0], info[rid]
        if rows:
            hdr = ("The following approvals are required for this document" if rtype(rid) in ("sop", "wi", "rec") else "The following approvals are required to transition to status") + f' "{to}":'
            tbl = "\n".join(f"| {role} | {ICON[st]}{(' by ' + who) if who and st == 'signed' else ''}{(': ' + why) if why else ''} |" for role, st, who, why in rows)
            out.append(f"{hdr}\n\n| Approvals | Status |\n|:---:|:---|\n{tbl}\n")
            out.append("Sign with `python3 tools/sign.py <role> " + f"{rid} {to}`, then commit and push the file in `signatures/`.\n")
        else:
            out.append(f'No approvals are required for "{to}".\n')
    elif len(sel) != 1:
        out.append("_Tick one state to see the approvals required._\n")
    return "\n".join(out) + extra


def patch_body(repo, pr, text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(text)
    r = sh("gh", "api", "-X", "PATCH", f"repos/{repo}/pulls/{pr}", "-F", f"body=@{f.name}")
    if r.returncode:
        print("note: could not update the description:", r.stderr.strip())
    return r.returncode == 0


def set_labels(repo, pr, wanted):
    r = sh("gh", "pr", "view", str(pr), "-R", repo, "--json", "labels", "-q", ".labels[].name")
    have = [x for x in r.stdout.split("\n") if x.startswith("lc: ")]
    for lab in have:
        if lab not in wanted:
            sh("gh", "pr", "edit", str(pr), "-R", repo, "--remove-label", lab)
    for lab in wanted:
        if lab not in have:
            sh("gh", "pr", "edit", str(pr), "-R", repo, "--add-label", lab)


def pr_approvals(repo, pr, head, author):
    r = sh("gh", "api", "--paginate", f"repos/{repo}/pulls/{pr}/reviews", "--jq", ".[] | {u: .user.login, s: .state, c: .commit_id}")
    last = {}
    for line in r.stdout.splitlines():
        v = json.loads(line)
        if v["s"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            last[v["u"]] = v
    ok = [u for u, v in last.items() if v["s"] == "APPROVED" and u != author and u in ROLES["github_approvers"] and v["c"] == head]
    stale = [u for u, v in last.items() if v["s"] == "APPROVED" and u != author and v["c"] != head]
    return ok, stale


def comment(repo, pr, text):
    r = sh("gh", "api", f"repos/{repo}/issues/{pr}/comments", "--jq", f'.[] | select(.body | startswith("{MARK}")) | .id')
    cid = r.stdout.split()[0] if r.stdout.split() else None
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(MARK + "\n" + text)
    if cid:
        sh("gh", "api", "-X", "PATCH", f"repos/{repo}/issues/comments/{cid}", "-F", f"body=@{f.name}")
    else:
        sh("gh", "api", f"repos/{repo}/issues/{pr}/comments", "-F", f"body=@{f.name}")


def write_audit(base, pr, author, moves, approvers):
    sh("git", "fetch", "origin", base)
    sh("git", "checkout", "-B", base, f"origin/{base}")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    for rid, (to, rows) in moves.items():
        p = pathlib.Path(lc.find_record(rid)[:-3] + ".audit.json")
        doc = json.load(open(p)) if p.exists() else {"schema": "demo/audit/1", "record": rid, "entries": []}
        e = {"at": now, "pr": pr, "submitted_by": author, "required_roles": [r[0] for r in rows], "record_state": to,
             "record_sha256": lc.sha256_file(lc.find_record(rid)), "pr_approved_by": approvers}
        if rows:
            e["signatures"] = {role: {"file": lc.sig_path(role, rid), "signer": who, "sha256": lc.sha256_file(lc.sig_path(role, rid))} for role, st, who, why in rows}
        doc["entries"].append(e)
        p.write_text(json.dumps(doc, indent=2) + "\n")
        sh("git", "add", str(p))
    sh("python3", "tools/build_portal.py", "--readme")
    sh("git", "add", "README.md")
    sh("git", *GIT_ID, "commit", "-m", f"Audit trail: PR #{pr} ({', '.join(moves)})")
    for _ in range(2):
        if sh("git", "push", "origin", f"HEAD:{base}").returncode == 0:
            return True
        sh("git", "pull", "--rebase", "origin", base)
    return False


def main():
    ev = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["pull_request"]
    pr, base, repo, author, head = ev["number"], ev["base"]["ref"], os.environ["GITHUB_REPOSITORY"], ev["user"]["login"], ev["head"]["sha"]
    if sh("gh", "pr", "view", str(pr), "-R", repo, "--json", "state", "-q", ".state").stdout.strip() != "OPEN":
        print("PR is not open: nothing to do.")
        return 0
    changed = sorted({pathlib.Path(f).stem for f in sh("git", "diff", "--name-only", f"origin/{base}...HEAD").stdout.split()
                      if re.fullmatch(r"records/[\w-]+/[\w-]+\.md", f) and lc.find_record(pathlib.Path(f).stem)})
    if not changed:
        set_labels(repo, pr, [])
        print("No records changed: no lifecycle check needed.")
        return 0
    ticks, notes = parse_body(ev.get("body") or "")
    cur = {r: state_at(base, r) for r in changed}
    for r in changed:  # attached documents are shown under their change control even when unchanged
        for d in lc.attached(r):
            cur.setdefault(d, state_at(base, d))
    lines, fail, moves, info, effective = [], False, {}, {}, {}
    for rid in changed:
        t, sel, c = T[rtype(rid)], ticks.get(rid, []), cur[rid]
        imp = t.get("implied")
        if imp:
            sel = [imp]
        elif c is None and not sel:
            sel = [t["states"][0]]  # a new record starts at its first state without a click
        ticks[rid] = sel
        if len(sel) != 1:
            lines.append(f"FAIL  {rid}: tick exactly one requested state (found {len(sel)}).")
            fail = True
            continue
        to = sel[0]
        if imp:
            ok, why = True, ""
        elif c is None:
            ok, why = to == t["states"][0], f"a new record must start at {t['states'][0]}"
        else:
            nxt = t["transitions"][c]
            ok, why = (to == c or to in nxt), (f"{c} is final." if not nxt else f"not allowed. From {c} the next state can be: {', '.join(nxt)}")
        lines.append(f"{'OK  ' if ok else 'FAIL'}  {rid}  {c or 'none'} -> {to}" + ("" if ok else f": {why}"))
        fail |= not ok
        effective[rid] = to if ok else c
        if ok and (c != to or imp):
            author_id = lc.front(open(lc.find_record(rid)).read()).get("author", "")
            rows = []
            for role in t["approvals"].get(to, []):
                st, why2, who = lc.verify(lc.sig_path(role, rid), rid, role, to, author_id)
                rows.append((role, st, who, why2))
            info[rid] = rows
            moves[rid] = (to, rows)
        else:
            info[rid] = []
    for rid in changed:  # change controls: attached documents must be Approved first
        if rtype(rid) == "change-control" and (ticks.get(rid) or [None])[0] in lc.CFG["requires_docs_approved_for"] and effective.get(rid) != cur[rid]:
            for d in lc.attached(rid):
                s = effective.get(d, cur.get(d))
                if d in moves and any(r[1] != "signed" for r in moves[d][1]):
                    s = "awaiting signatures"
                bad = s != "Approved"
                lines.append(f"{'FAIL' if bad else 'OK  '}  {rid}: attached {d} is {s or 'not yet created'}" + (" (needs Approved before Implemented)" if bad else ""))
                fail |= bad
    set_labels(repo, pr, [f"lc: {r} / {lc.slug(ticks[r][0])}" for r in changed if len(ticks.get(r, [])) == 1 and not T[rtype(r)].get("implied")][:20])
    body = ["<!-- lifecycle-form -->\n## Lifecycle request\n\nOne section per record in this PR. Tick the requested state; approvals update as signature files are pushed.\n"]
    ccs = [r for r in changed if rtype(r) == "change-control"]
    docs_done = set()
    for rid in ccs:
        att = lc.attached(rid)
        body.append(section(rid, ticks, cur[rid], info))
        if att:
            body.append("Documents attached to this change control:\n\n" + "\n".join(f"- {d}: {'awaiting signatures' if d in moves and any(r[1] != 'signed' for r in moves[d][1]) else (effective.get(d, cur.get(d)) or 'not yet created')}" + (" (in this PR)" if d in changed else "") for d in att) + "\n")
        for d in att:
            if d in changed:
                body.append(section(d, ticks, cur[d], info))
                docs_done.add(d)
        body.append("---\n")
    for rid in changed:
        if rid not in ccs and rid not in docs_done:
            body.append(section(rid, ticks, cur[rid], info) + "\n---\n")
    body.append("## Notes for approvers\n\n" + notes + "\n")
    new = "\n".join(body)
    if new.strip() != (ev.get("body") or "").strip() and patch_body(repo, pr, new):
        print("Description rebuilt from the attached records.")
    sigs = [(rid, role, st, why) for rid, (to, rows) in moves.items() for role, st, who, why in rows]
    missing = [f"{role} for {rid}" for rid, role, st, why in sigs if st != "signed"]
    appr, stale = pr_approvals(repo, pr, head, author)
    sl = ["", "Signature files"] + [f"  {'OK     ' if st == 'signed' else st.upper().ljust(7)} {lc.sig_path(role, rid)}" + (f"  ({why})" if why else "") for rid, role, st, why in sigs]
    if not sigs:
        sl.append("  none required")
    sl += ["", f"PR approval at the head commit (given last): {', '.join(appr) or 'none yet'}"]
    if stale:
        sl.append(f"  Stale approvals (given before the latest push, not counted): {', '.join(stale)}")
    if fail:
        verdict = "BLOCKED: fix the failures above."
    elif missing:
        verdict = "WAITING for signatures: " + "; ".join(missing)
    elif not appr:
        verdict = "WAITING for PR approval (approve last, after all signatures are pushed)."
    else:
        verdict = "READY: rules pass, signatures verify, PR approved. Merging, then writing the audit trail."
    text = f"Lifecycle gate, PR #{pr}\n" + "\n".join(lines + sl + ["", verdict])
    print(text)
    comment(repo, pr, "```\n" + text + "\n```\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
    if fail or missing or not appr:
        return 1
    m = sh("gh", "pr", "merge", str(pr), "-R", repo, "--merge")
    if m.returncode:
        print("Merge failed:", m.stderr.strip())
        return 1
    ok = write_audit(base, pr, author, moves, appr)
    print("Audit trail written to main." if ok else "Audit write failed: reconcile needed.")
    if ok:
        sh("gh", "workflow", "run", "portal.yml", "-R", repo, "--ref", base)
    comment(repo, pr, "```\n" + text.replace(verdict, "MERGED. Audit trail written to main." if ok else "MERGED. Audit write FAILED: needs reconcile.") + "\n```\n")
    return 0 if ok else 1


sys.exit(main())
