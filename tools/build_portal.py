"""Build the lifecycle log portal: one self-contained site/index.html from the records, their audit files
and lifecycles.json. Open PRs and their requested states are added when `gh` can read them."""
import json, pathlib, re, subprocess, datetime, os

L = json.load(open("lifecycles.json"))
# Documents (SOP, WI, REC) have no lifecycle: they live in the main document portal, not this one.
FAMS = {k: v for k, v in L["types"].items() if not v.get("implied")}


def front(path):
    m = re.match(r"---\n(.*?)\n---", path.read_text(), re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)) if m else {}


records = []
for fam, f in FAMS.items():
    for md in sorted(pathlib.Path(f"records/{fam}").glob("*.md")):
        fm = front(md)
        a = pathlib.Path(md).with_suffix(".audit.json")
        entries = json.load(open(a))["entries"] if a.exists() else []
        last = entries[-1] if entries else {}
        records.append({"id": fm.get("id", md.stem), "title": fm.get("title", ""), "owner": fm.get("owner", ""),
                        "family": fam, "state": last.get("record_state", "(no audit entry)"),
                        "at": last.get("at", ""), "pr": last.get("pr", ""), "by": last.get("submitted_by", ""),
                        "change": fm.get("change", ""), "signed": ", ".join(f"{k}:{v['signer']}" for k, v in last.get("signatures", {}).items()),
                        "final": not f["transitions"].get(last.get("record_state"), [1]), "history": entries,
                        "path": str(md)})
prs = []
try:
    out = subprocess.run(["gh", "pr", "list", "-R", os.environ.get("GITHUB_REPOSITORY", "AgFox70/lifecycle-log-demo"), "--state", "open",
                          "--json", "number,title,author,labels,url,updatedAt"], capture_output=True, text=True, timeout=30)
    if out.returncode == 0:
        for p in json.loads(out.stdout):
            prs.append({"n": p["number"], "title": p["title"], "by": p["author"]["login"], "url": p["url"],
                        "labels": [x["name"] for x in p["labels"] if x["name"].startswith("lc: ")], "at": p["updatedAt"][:10]})
except Exception:
    pass
data = {"families": {k: {"name": v["name"], "states": v["states"], "transitions": v["transitions"], "approvals": v["approvals"]} for k, v in FAMS.items()},
        "records": records, "prs": prs, "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
html = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Lifecycle log portal (demo)</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#f6f7f9;--ink:#1c2430;--mut:#667085;--line:#e3e6ea;--acc:#1d4ed8}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--ink);display:flex;min-height:100vh}
nav{width:230px;background:#101828;color:#d0d5dd;padding:16px 0;flex:none}nav h1{font-size:15px;margin:0 16px 12px;color:#fff}
nav a{display:flex;justify-content:space-between;padding:8px 16px;color:inherit;text-decoration:none;border-left:3px solid transparent}
nav a:hover{background:#1d2939}nav a.on{background:#1d2939;border-color:#60a5fa;color:#fff}nav .n{background:#344054;border-radius:9px;padding:0 7px;font-size:12px}
main{flex:1;padding:20px 28px;min-width:0}h2{margin:0 0 4px}.sub{color:var(--mut);margin-bottom:14px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}input,select{padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:#fff;font:inherit}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0 4px}.chip{padding:2px 9px;border-radius:12px;font-size:12px;border:1px solid var(--line);background:#fff;cursor:pointer}
.chip.on{outline:2px solid var(--acc)}.arrow{color:var(--mut)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f2f4f7;cursor:pointer;white-space:nowrap;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
tr.rec{cursor:pointer}tr.rec:hover{background:#f9fafb}.badge{display:inline-block;padding:1px 9px;border-radius:10px;font-size:12px;font-weight:600}
.final{border:1px solid #b42318}.hist td{background:#fafbfc;font-size:13px}.mut{color:var(--mut)}.pill{font-size:11px;background:#eef2ff;color:#3730a3;border-radius:8px;padding:0 6px;margin-left:4px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:14px 0}.cards{display:flex;gap:10px;flex-wrap:wrap}.stat{background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px 14px;min-width:110px}
.stat b{font-size:20px;display:block}a{color:var(--acc)}footer{color:var(--mut);margin-top:18px;font-size:12px}
</style></head><body><nav><h1>Lifecycle log</h1><div id="nav"></div></nav><main id="main"></main>
<script>
const D=__DATA__;const $=s=>document.querySelector(s);
const palette=["#e0e7ff","#fef3c7","#dcfce7","#fee2e2","#cffafe","#fae8ff","#ffedd5","#e2e8f0"];
function color(fam,state){const i=D.families[fam]?.states.indexOf(state);return palette[(i<0?7:i)%palette.length]}
let view=location.hash.slice(1)||"all",q="",st="",own="",sortk="id",dir=1,openId=null;
function fams(){return Object.keys(D.families)}
function nav(){let h=`<a href="#all" class="${view=="all"?"on":""}">All records<span class="n">${D.records.length}</span></a>`;
 h+=fams().map(f=>`<a href="#${f}" class="${view==f?"on":""}">${D.families[f].name}<span class="n">${D.records.filter(r=>r.family==f).length}</span></a>`).join("");
 h+=`<a href="#prs" class="${view=="prs"?"on":""}">Pending PRs<span class="n">${D.prs.length}</span></a>`;$("#nav").innerHTML=h}
function flow(f){const F=D.families[f];return `<div class="flow">`+F.states.map(s=>`<span class="chip ${st==s?"on":""}" data-s="${s}" style="background:${color(f,s)}" title="next: ${F.transitions[s].join(", ")||"none (final)"}">${s}</span>`).join('<span class="arrow">&rarr;</span>')+`</div><div class="mut">Click a state to filter. Click a state for its approvals: ${Object.entries(F.approvals).map(a=>a[0]+" needs "+a[1].join(", ")).join("; ")||"none"}.</div>`}
function rows(){let r=D.records.filter(x=>view=="all"||x.family==view);
 if(q)r=r.filter(x=>(x.id+x.title+x.owner+x.by).toLowerCase().includes(q.toLowerCase()));
 if(st)r=r.filter(x=>x.state==st);if(own)r=r.filter(x=>x.owner==own);
 return r.sort((a,b)=>(String(a[sortk]).localeCompare(String(b[sortk]),undefined,{numeric:true}))*dir)}
function table(r){const cols=[["id","ID"],["title","Title"],["family","Type"],["state","State"],["at","Last change"],["pr","PR"],["change","Change"],["signed","Signatures"],["owner","Owner"]];
 let h=`<table><tr>${cols.map(c=>`<th data-k="${c[0]}">${c[1]}${sortk==c[0]?(dir>0?" ▲":" ▼"):""}</th>`).join("")}</tr>`;
 for(const x of r){h+=`<tr class="rec" data-id="${x.id}"><td><b>${x.id}</b></td><td>${x.title}</td><td>${D.families[x.family].name}</td><td><span class="badge ${x.final?"final":""}" style="background:${color(x.family,x.state)}">${x.state}</span></td><td>${x.at}</td><td>${x.pr?"#"+x.pr:""}</td><td>${x.change||""}</td><td>${x.signed||""}</td><td>${x.owner}</td></tr>`;
  if(openId==x.id)h+=`<tr class="hist"><td colspan="10"><b>Audit trail</b> (${x.path.replace(".md",".audit.json")})<table style="margin-top:6px"><tr><th>When</th><th>State</th><th>PR</th><th>Submitted by</th><th>Signatures</th><th>PR approved by</th></tr>${x.history.map(e=>`<tr><td>${e.at}</td><td>${e.record_state}</td><td>#${e.pr}</td><td>${e.submitted_by}</td><td>${Object.entries(e.signatures||{}).map(a=>a[0]+": "+a[1].signer).join(", ")||(e.required_roles||[]).length?"":"none required"}</td><td>${(e.pr_approved_by||[]).join(", ")}</td></tr>`).join("")}</table></td></tr>`}
 return h+"</table>"+(r.length?"":'<p class="mut">No records match.</p>')}
function render(){nav();const m=$("#main");
 if(view=="prs"){m.innerHTML=`<h2>Pending pull requests</h2><div class="sub">Open PRs and the lifecycle state they request</div>`+(D.prs.length?`<table><tr><th>PR</th><th>Title</th><th>Requested</th><th>By</th><th>Updated</th></tr>${D.prs.map(p=>`<tr><td><a href="${p.url}">#${p.n}</a></td><td>${p.title}</td><td>${p.labels.map(l=>`<span class="pill">${l.replace("lc: ","")}</span>`).join(" ")||'<span class="mut">none yet</span>'}</td><td>${p.by}</td><td>${p.at}</td></tr>`).join("")}</table>`:'<p class="mut">No open PRs (or not readable at build time).</p>')+foot();return}
 const f=view=="all"?null:view;const set=D.records.filter(x=>!f||x.family==f);
 const states=[...new Set(set.map(x=>x.state))];const owners=[...new Set(set.map(x=>x.owner))];
 const counts=states.map(s=>`<div class="stat"><b>${set.filter(x=>x.state==s).length}</b>${s}</div>`).join("");
 m.innerHTML=`<h2>${f?D.families[f].name:"All records"}</h2><div class="sub">Current state is the last audit trail entry</div>${f?flow(f):""}<div class="cards">${counts}</div>
 <div class="bar"><input id="q" placeholder="Search id, title, owner, submitter" value="${q}"><select id="st"><option value="">Any state</option>${states.map(s=>`<option ${st==s?"selected":""}>${s}</option>`).join("")}</select><select id="own"><option value="">Any owner</option>${owners.map(s=>`<option ${own==s?"selected":""}>${s}</option>`).join("")}</select><button id="clr">Clear</button></div>`+table(rows())+foot();
 $("#q").oninput=e=>{q=e.target.value;const p=e.target.selectionStart;render();$("#q").focus();$("#q").setSelectionRange(p,p)};
 $("#st").onchange=e=>{st=e.target.value;render()};$("#own").onchange=e=>{own=e.target.value;render()};$("#clr").onclick=()=>{q=st=own="";render()};
 m.querySelectorAll("th[data-k]").forEach(t=>t.onclick=()=>{const k=t.dataset.k;dir=sortk==k?-dir:1;sortk=k;render()});
 m.querySelectorAll("tr.rec").forEach(t=>t.onclick=()=>{openId=openId==t.dataset.id?null:t.dataset.id;render()});
 m.querySelectorAll(".chip").forEach(c=>c.onclick=()=>{st=st==c.dataset.s?"":c.dataset.s;render()})}
function foot(){return `<footer>Built ${D.built}. Demo data: fictional.</footer>`}
window.onhashchange=()=>{view=location.hash.slice(1)||"all";st=own=q="";openId=null;render()};render();
</script></body></html>"""
pathlib.Path("site").mkdir(exist_ok=True)
pathlib.Path("site/index.html").write_text(html.replace("__DATA__", json.dumps(data)))
print(f"portal built: {len(records)} records, {len(prs)} open PRs -> site/index.html")


def readme_log():
    """Markdown log of every record by type, written into README.md between the LOG markers."""
    out = [f"_Updated {data['built']} from the audit trail. {len(records)} records._\n"]
    for fam, f in FAMS.items():
        rs = [r for r in records if r["family"] == fam]
        out.append(f"### {f['name']} ({len(rs)})\n")
        if not rs:
            out.append("_None yet._\n")
            continue
        out.append("| ID | Title | State | Last change | Signatures |\n|---|---|---|---|---|")
        out += [f"| {r['id']} | {r['title']} | **{r['state']}** | {r['at']} (PR #{r['pr']}) | {r['signed'] or '-'} |" for r in rs]
        out.append("")
    return "\n".join(out)


if "--readme" in __import__("sys").argv:
    rd = pathlib.Path("README.md").read_text()
    new = re.sub(r"(<!-- LOG:START -->).*?(<!-- LOG:END -->)", lambda m: m.group(1) + "\n" + readme_log() + "\n" + m.group(2), rd, flags=re.S)
    pathlib.Path("README.md").write_text(new)
    print("README log updated")
