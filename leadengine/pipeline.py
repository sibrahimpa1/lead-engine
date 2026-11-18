"""One batch: rows -> people -> enrich -> score -> route -> CRM upsert -> draft -> checks -> approval queue."""
from __future__ import annotations

from pathlib import Path

from . import normalize as N
from .crm import FakeCRM
from .dedupe import group, load_rows
from .drafts import ReplayDrafter, check
from .qualify import Firmographics, Router, load_icp, score

ROOT = Path(__file__).resolve().parent.parent


def run(rows: list, crm, drafter=None, icp: dict | None = None, firmo: Firmographics | None = None) -> dict:
    icp = icp or load_icp()
    firmo = firmo or Firmographics()
    drafter = drafter or ReplayDrafter()
    router = Router(icp)
    people = group(rows)
    results = []
    for lead in people:
        f = {**lead.fields, "id": lead.id}
        enrich = {} if N.is_freemail(f["email"]) else firmo.lookup(lead.domain)
        existing = crm.find_contact(f["email"])
        company_rec = crm.find_company(lead.domain) if lead.domain and not N.is_freemail(f["email"]) else None
        s = score(f, enrich, icp, existing)
        account_owner = (existing or {}).get("owner") or (company_rec or {}).get("owner")
        if "test or junk submission" in s["disqualified"] or "competitor domain" in s["disqualified"]:
            account_owner = None
        route = router.route(f, s, account_owner, "" if N.is_freemail(f["email"]) else lead.domain)
        crm_op = None
        if not ({"test or junk submission", "competitor domain"} & set(s["disqualified"])):
            props = {"email": f["email"], "firstname": f["first_name"], "lastname": f["last_name"],
                     "jobtitle": f["title"], "company": f["company"], "country": f["country"], "phone": f["phone"],
                     "lead_score": str(s["score"]), "owner": route["owner"] or "", "lead_source": ",".join(f["sources"])}
            crm_op = crm.upsert_contact(props)
        draft, problems = None, []
        if s["qualified"] and route["owner"] and not (existing or {}).get("lifecycle") == "customer":
            draft = drafter.draft(f, route)
            problems = check(draft, f)
        status = ("disqualified" if s["disqualified"] else "nurture" if not s["qualified"]
                  else "queued" if not route["owner"] else "needs_edit" if problems else "pending_approval")
        results.append({"id": lead.id, "merged": lead.merged_ids, "merge_reasons": lead.reasons, "lead": f,
                        "enrichment": enrich, "existing_contact": existing, "existing_company": company_rec,
                        "score": s, "route": route, "crm": crm_op, "draft": draft, "draft_problems": problems,
                        "status": status})
    crm.save()
    ops = [r["crm"]["op"] for r in results if r["crm"]]
    summary = {"rows": len(rows), "people": len(people), "duplicates_merged": len(rows) - len(people),
               "qualified": sum(r["score"]["qualified"] for r in results),
               "hot": sum(r["score"]["hot"] for r in results),
               "disqualified": sum(1 for r in results if r["score"]["disqualified"]),
               "crm": {k: ops.count(k) for k in ("create", "update", "noop")},
               "drafts_pending": sum(r["status"] == "pending_approval" for r in results),
               "drafts_blocked": sum(r["status"] == "needs_edit" for r in results),
               "owners": dict(router.load)}
    return {"summary": summary, "results": results}


def demo(state_dir: Path) -> dict:
    """Run the batch twice against the same CRM state: the second run must write nothing."""
    rows = load_rows(ROOT / "data" / "leads.csv")
    seed = ROOT / "data" / "crm_seed.json"
    state = state_dir / "crm_state.json"
    if state.exists():
        state.unlink()
    first = run(rows, FakeCRM(seed=seed, state=state))
    second = run(rows, FakeCRM(seed=seed, state=state))
    return {"first": first, "second": second}
