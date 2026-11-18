"""Build the static live demo from the demo report: one HTML file, inline CSS and JS, no CDNs."""
from __future__ import annotations

import json
from pathlib import Path

from .qualify import load_icp


def build(report: dict, out: Path) -> Path:
    data = {"run1": report["first"], "run2": report["second"]["summary"], "icp": load_icp()}
    html = TEMPLATE.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lead engine: demo</title>
<style>
:root{--bg:#f5f4f0;--panel:#fff;--ink:#16171d;--muted:#676459;--line:#e4e1d8;--accent:#0f62fe;--accent-soft:#e7efff;
--ok:#15803d;--ok-soft:#e7f5ec;--warn:#a16207;--warn-soft:#fdf4dc;--bad:#b91c1c;--bad-soft:#fdeaea;--code:#f2f1ec}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.banner{background:#16171d;color:#f5f4f0;font-size:13px;text-align:center;padding:7px 12px}
header{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:16px 28px;background:var(--panel);border-bottom:1px solid var(--line)}
.brand{font-weight:800;font-size:18px}.brand small{display:block;font-weight:500;font-size:13px;color:var(--muted)}
nav a{display:inline-block;padding:7px 12px;border-radius:9px;color:var(--ink);font-weight:600;font-size:14px}nav a.on{background:var(--accent-soft);color:var(--accent)}
main{max-width:1200px;margin:0 auto;padding:24px 28px 60px}
h1{font-size:25px;margin:0 0 6px;letter-spacing:-.02em}h2{font-size:17px;margin:24px 0 10px}.lede{color:var(--muted);max-width:820px;margin:0 0 16px}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:14px 0 20px}.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi b{display:block;font-size:24px}.kpi span{font-size:12.5px;color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:9px 11px;border-top:1px solid var(--line);font-size:14px;vertical-align:top}th{background:#faf9f6;border-top:0;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
td.n{text-align:right;font-variant-numeric:tabular-nums}tr.click{cursor:pointer}tr.click:hover td{background:#fafaf7}
.pill{display:inline-block;font-size:12px;font-weight:650;padding:2px 9px;border-radius:999px;white-space:nowrap}
.s-pending_approval{background:var(--accent-soft);color:var(--accent)}.s-needs_edit{background:var(--bad-soft);color:var(--bad)}.s-disqualified{background:#eee;color:#555}
.s-nurture{background:var(--warn-soft);color:var(--warn)}.s-queued{background:var(--warn-soft);color:var(--warn)}.s-sent{background:var(--ok-soft);color:var(--ok)}.s-approved{background:var(--ok-soft);color:var(--ok)}
.bar{height:8px;border-radius:4px;background:#ecebe5;overflow:hidden;width:90px;display:inline-block;vertical-align:middle;margin-right:6px}.bar i{display:block;height:100%;background:var(--accent)}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:16px}.panel h3{margin:0 0 10px;font-size:15px}
.kv{display:grid;grid-template-columns:130px 1fr;gap:5px 12px;font-size:14px}.kv dt{color:var(--muted)}.kv dd{margin:0}
.parts div{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding:6px 0;font-size:14px}.parts div:first-child{border-top:0}
.pos{color:var(--ok);font-weight:650}.neg{color:var(--bad);font-weight:650}
.mail{background:var(--code);border-radius:10px;padding:12px 14px;white-space:pre-wrap;font-size:14px}
.check{font-size:13.5px;padding:4px 0}.check.bad{color:var(--bad)}.check.ok{color:var(--ok)}
.btns{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}button{font:inherit;font-weight:650;border-radius:9px;border:1px solid var(--line);background:var(--panel);padding:8px 14px;cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}button:disabled{opacity:.45;cursor:not-allowed}
.note{font-size:13px;color:var(--muted)}.src{font-size:12px;color:var(--muted)}
.flow{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 4px}.flow span{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:7px 11px;font-size:13.5px}.flow i{font-style:normal;color:var(--muted);align-self:center}
.reps{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.rep{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
.rep b{display:block}.cap{height:10px;border-radius:5px;background:#ecebe5;overflow:hidden;margin:8px 0 4px}.cap i{display:block;height:100%;background:var(--accent)}
code{font:13px ui-monospace,Menlo,monospace;background:var(--code);padding:1px 5px;border-radius:5px}
@media (max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.grid,.reps{grid-template-columns:1fr}main{padding:18px 16px 40px}header{padding:12px 16px}.hide-sm{display:none}}
</style></head><body>
<div class="banner">Demo on synthetic data: made-up companies and people on .example domains, a fake HubSpot, recorded email drafts</div>
<header><div class="brand">Lead engine<small>Dedupe, enrich, score, route, write to the CRM, draft the first email</small></div>
<nav id="nav"><a href="#inbox">Inbox</a><a href="#approvals">Approvals</a><a href="#routing">Routing</a><a href="#runs">Idempotency</a></nav></header>
<main id="app"></main>
<script>
const D=/*__DATA__*/null;const R=D.run1.results,S=D.run1.summary;
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const LBL={pending_approval:"waiting for approval",needs_edit:"draft blocked",disqualified:"disqualified",nurture:"nurture",queued:"queued: no free rep",approved:"approved",sent:"sent"};
const ST={};try{Object.assign(ST,JSON.parse(localStorage.getItem("le-approvals")||"{}"))}catch(e){}
const save=()=>{try{localStorage.setItem("le-approvals",JSON.stringify(ST))}catch(e){}};
const status=r=>ST[r.id]||r.status;const pill=s=>`<span class="pill s-${s}">${esc(LBL[s]||s)}</span>`;
const byId=id=>R.find(r=>r.id===id);
function kpis(){return `<div class="kpis"><div class="kpi"><b>${S.rows}</b><span>rows in</span></div><div class="kpi"><b>${S.people}</b><span>people after dedupe</span></div>
<div class="kpi"><b>${S.qualified}</b><span>qualified</span></div><div class="kpi"><b>${S.hot}</b><span>hot (score ${D.icp.hot_threshold}+)</span></div>
<div class="kpi"><b>${S.drafts_pending}</b><span>drafts waiting for a person</span></div><div class="kpi"><b>${S.drafts_blocked}</b><span>drafts blocked by checks</span></div></div>`}
function inbox(){
  const rows=R.slice().sort((a,b)=>b.score.score-a.score.score).map(r=>{const l=r.lead;return `<tr class="click" onclick="location.hash='#lead/${r.id}'">
  <td><a href="#lead/${r.id}">${r.id}</a>${r.merged.length>1?`<div class="src">+${r.merged.length-1} merged</div>`:""}</td><td><b>${esc(l.first_name)} ${esc(l.last_name)}</b><div class="src">${esc(l.title)}</div></td>
  <td>${esc(l.company)}<div class="src">${esc(l.country)}</div></td><td><span class="bar"><i style="width:${r.score.score}%"></i></span>${r.score.score}</td>
  <td>${esc(r.route.owner_name||"-")}</td><td>${pill(status(r))}</td><td class="hide-sm src">${esc(r.crm?r.crm.op:"not written")}</td></tr>`}).join("");
  return `<h1>Inbound leads, handled in one pass</h1><p class="lede">${S.rows} form, webinar, chat and CSV rows become ${S.people} people. Each one is enriched, scored with reasons, routed to an owner, written to the CRM and given a first email that waits for a person to approve it.</p>
  <div class="flow"><span>Rows</span><i>→</i><span>Normalise and dedupe</span><i>→</i><span>Enrich (with source)</span><i>→</i><span>Score in code, with reasons</span><i>→</i><span>Route by account, territory, load</span><i>→</i><span>Upsert to CRM, idempotent</span><i>→</i><span>Model drafts, code checks</span><i>→</i><span>Person approves</span></div>
  ${kpis()}<table><thead><tr><th>Lead</th><th>Person</th><th>Company</th><th>Score</th><th>Owner</th><th>Status</th><th class="hide-sm">CRM</th></tr></thead><tbody>${rows}</tbody></table>`}
function lead(id){
  const r=byId(id);if(!r)return "<p>Unknown lead.</p>";const l=r.lead,st=status(r);
  const en=Object.entries(r.enrichment||{}).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(Array.isArray(v.value)?v.value.join(", ")||"-":v.value)}<div class="src">${esc(v.source)}</div></dd>`).join("");
  const parts=r.score.disqualified.length?r.score.disqualified.map(d=>`<div><span>${esc(d)}</span><span class="neg">disqualified</span></div>`).join(""):
    r.score.parts.map(p=>`<div><span>${esc(p.label)}</span><span class="${p.points<0?"neg":"pos"}">${p.points>0?"+":""}${p.points}</span></div>`).join("")+`<div><b>Total (0-100)</b><b>${r.score.score}</b></div>`;
  const merged=r.merge_reasons.length?r.merge_reasons.map(m=>`<div class="note">${esc(m)}</div>`).join(""):'<div class="note">No duplicates.</div>';
  const checks=r.draft?(r.draft_problems.length?r.draft_problems.map(p=>`<div class="check bad">✕ ${esc(p)}</div>`).join(""):'<div class="check ok">✓ greets by name and names the company · ✓ every number comes from the lead · ✓ no promises sales can\'t make · ✓ no template leftovers · ✓ under 120 words</div>'):"";
  const blocked=r.draft_problems.length>0;
  const draft=r.draft?`<div class="panel"><h3>First email (drafted by the model, checked by code)</h3><div class="note">Subject: ${esc(r.draft.subject)}</div><div class="mail">${esc(r.draft.body)}</div>${checks}
   <div class="btns"><button class="primary" ${blocked||st!=="pending_approval"?"disabled":""} onclick="act('${r.id}','approved')">Approve</button>
   <button ${st!=="approved"?"disabled":""} onclick="act('${r.id}','sent')">Send</button><button ${ST[r.id]?"":"disabled"} onclick="act('${r.id}',null)">Reset</button></div>
   <p class="note">${blocked?"Blocked: a person edits the draft before it can be approved.":st==="sent"?"Sent once. Sending the same text to the same lead again is refused (idempotency key).":"Nothing is sent until a person approves this exact text."}</p></div>`:
   `<div class="panel"><h3>No email</h3><p class="note">${r.score.disqualified.length?"Disqualified leads get no sales email.":!r.route.owner?"No owner yet, so no email.":"Not qualified: goes to the nurture list."}</p></div>`;
  return `<p><a href="#inbox">← Inbox</a></p><h1>${esc(l.first_name)} ${esc(l.last_name)} · ${esc(l.company)}</h1><p class="lede">${esc(l.title)} · ${esc(l.email)} · ${pill(st)}</p>
  <div class="grid"><div><div class="panel"><h3>Lead after merge</h3><dl class="kv"><dt>Sources</dt><dd>${esc(l.sources.join(", "))}</dd><dt>Rows</dt><dd>${esc(r.merged.join(", "))}</dd><dt>Phone</dt><dd>${esc(l.phone||"-")}</dd><dt>Intent</dt><dd>${esc(l.page||"-")}</dd><dt>Message</dt><dd>${esc(l.message||"-")}</dd></dl>${merged}</div>
  <div class="panel"><h3>Enrichment</h3>${en?`<dl class="kv">${en}</dl>`:'<p class="note">Nothing found (personal email or unknown domain). Nothing is guessed.</p>'}</div>
  <div class="panel"><h3>Routing and CRM</h3><dl class="kv"><dt>Owner</dt><dd>${esc(r.route.owner_name||"none")}</dd><dt>Why</dt><dd>${esc(r.route.reason)}</dd>
  <dt>CRM write</dt><dd>${r.crm?`${esc(r.crm.op)} ${esc(r.crm.id)}${r.crm.fields.length?`<div class="src">fields: ${esc(r.crm.fields.join(", "))}</div>`:""}`:"not written (junk or competitor)"}</dd>
  ${r.existing_contact?`<dt>Already in CRM</dt><dd>${esc(r.existing_contact.id)}, owner ${esc(r.existing_contact.owner)}, ${esc(r.existing_contact.lifecycle)}<div class="src">owner is never overwritten</div></dd>`:""}</dl></div></div>
  <div><div class="panel"><h3>Score</h3><div class="parts">${parts}</div><p class="note">Weights live in icp.json. The model plays no part in the score.</p></div>${draft}</div></div>`}
function act(id,s){if(s)ST[id]=s;else delete ST[id];save();render()}
function approvals(){
  const q=R.filter(r=>r.draft).map(r=>`<tr class="click" onclick="location.hash='#lead/${r.id}'"><td><a href="#lead/${r.id}">${r.id}</a></td><td>${esc(r.lead.first_name)} ${esc(r.lead.last_name)}<div class="src">${esc(r.lead.company)}</div></td>
   <td>${esc(r.draft.subject)}</td><td>${esc(r.route.owner_name)}</td><td>${pill(status(r))}${r.draft_problems.length?`<div class="src">${esc(r.draft_problems[0])}</div>`:""}</td></tr>`).join("");
  return `<h1>Approval queue</h1><p class="lede">Every first email waits here. Drafts that fail a check are blocked before a person ever sees an Approve button. Approve and send work in this demo, and the state stays in your browser.</p>
  <table><thead><tr><th>Lead</th><th>Person</th><th>Subject</th><th>Owner</th><th>Status</th></tr></thead><tbody>${q}</tbody></table>`}
function routing(){
  const reps=D.icp.routing.reps;const load=S.owners;
  const cards=Object.entries(reps).map(([k,v])=>`<div class="rep"><b>${esc(v.name)}</b><span class="note">${esc(v.territory==="ALL"?"senior, all territories":v.territory)}</span>
   <div class="cap"><i style="width:${Math.min(100,load[k]/v.capacity*100)}%"></i></div><span class="note">${load[k]} of ${v.capacity} today</span></div>`).join("");
  const reasons={};R.forEach(r=>{const k=r.route.reason.replace(/\(score \d+\)/,"").trim();reasons[k]=(reasons[k]||0)+1});
  return `<h1>Routing</h1><p class="lede">Rules run in this order: existing account owner, the same company as an earlier lead in the batch, hot leads to the senior rep, then the territory rep with the lowest load. When everyone is full, the lead waits in a queue instead of going to someone over capacity.</p>
  <div class="reps">${cards}</div><h2>Why each lead went where it did</h2><table><thead><tr><th>Reason</th><th>Leads</th></tr></thead><tbody>${Object.entries(reasons).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<tr><td>${esc(k)}</td><td class="n">${v}</td></tr>`).join("")}</tbody></table>`}
function runs(){
  const a=S.crm,b=D.run2.crm;
  return `<h1>Safe to run twice</h1><p class="lede">The same batch was run twice against the same CRM. Upserts key on the canonical email and send only fields that changed, so the second run writes nothing. Existing owners are never overwritten.</p>
  <table><thead><tr><th>Run</th><th>Created</th><th>Updated</th><th>No change</th></tr></thead><tbody><tr><td>First run</td><td class="n">${a.create}</td><td class="n">${a.update}</td><td class="n">${a.noop}</td></tr><tr><td>Same batch again</td><td class="n">${b.create}</td><td class="n">${b.update}</td><td class="n">${b.noop}</td></tr></tbody></table>
  <h2>Duplicates caught</h2><table><thead><tr><th>Kept</th><th>Merged rows and why</th></tr></thead><tbody>${R.filter(r=>r.merge_reasons.length).map(r=>`<tr><td><a href="#lead/${r.id}">${r.id}</a></td><td>${r.merge_reasons.map(esc).join("<br>")}</td></tr>`).join("")}</tbody></table>`}
function render(){const h=decodeURIComponent(location.hash.slice(1))||"inbox";const [v,arg]=h.split("/");
  const views={inbox,approvals,routing,runs,lead:()=>lead(arg)};document.getElementById("app").innerHTML=(views[v]||inbox)();
  document.querySelectorAll("#nav a").forEach(a=>a.classList.toggle("on",a.getAttribute("href")==="#"+(v==="lead"?"inbox":v)));window.scrollTo(0,0)}
window.addEventListener("hashchange",render);render();
</script></body></html>
"""
