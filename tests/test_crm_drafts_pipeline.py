import json

from conftest import ROOT
from leadengine.crm import FakeCRM
from leadengine.dedupe import load_rows
from leadengine.drafts import Approvals, check
from leadengine.pipeline import demo, run

SEED = ROOT / "data" / "crm_seed.json"
LEAD = {"first_name": "Anna", "company": "Brightlane Logistics GmbH", "title": "Head of Operations",
        "message": "We route 4k parcels a day."}


def test_upsert_is_idempotent_and_protects_owner(tmp_path):
    crm = FakeCRM(seed=SEED, state=tmp_path / "s.json")
    a = crm.upsert_contact({"email": "new@x.example", "firstname": "N"})
    b = crm.upsert_contact({"email": "new@x.example", "firstname": "N"})
    assert (a["op"], b["op"]) == ("create", "noop")
    c = crm.upsert_contact({"email": "grace.lin@marrowsoft.example", "owner": "luka", "jobtitle": "Head of Sales Operations"})
    assert c["op"] == "update" and c["fields"] == ["jobtitle"]
    assert crm.find_contact("grace.lin@marrowsoft.example")["owner"] == "amira"


def test_second_run_writes_nothing(tmp_path):
    d = demo(tmp_path)
    assert d["first"]["summary"]["crm"]["create"] > 0
    assert d["second"]["summary"]["crm"] == {"create": 0, "update": 0, "noop": d["first"]["summary"]["crm"]["create"] + d["first"]["summary"]["crm"]["update"]}


def test_draft_checks():
    ok = {"subject": "Hi", "body": "Hi Anna, routing 4k parcels a day at Brightlane is a lot. Call next week?"}
    assert check(ok, LEAD) == []
    bad = {"subject": "Offer", "body": "Hello, we guarantee a 30% discount for {company}."}
    problems = " | ".join(check(bad, LEAD))
    for part in ("first name", "Brightlane", "'30'", "guarantee", "discount", "placeholder"):
        assert part in problems
    assert any("words" in p for p in check({"subject": "x", "body": "Anna Brightlane " + "word " * 130}, LEAD))


def test_nothing_sends_without_approval_and_never_twice(tmp_path):
    ap = Approvals(tmp_path / "a.json")
    draft = {"subject": "Hi", "body": "Hi Anna"}
    assert ap.send("L-1", "a@x.example", draft)["reason"] == "not approved"
    ap.decide("L-1", draft, True, "amira")
    assert ap.send("L-1", "a@x.example", {**draft, "body": "Hi Anna, edited"})["reason"] == "the text changed after approval"
    assert ap.send("L-1", "a@x.example", draft)["sent"] is True
    assert ap.send("L-1", "a@x.example", draft)["reason"].startswith("already sent")
    ap.decide("L-2", draft, False, "luka", "tone")
    assert ap.send("L-2", "b@x.example", draft)["sent"] is False


def test_pipeline_outcomes_on_the_demo_data(tmp_path):
    out = run(load_rows(ROOT / "data" / "leads.csv"), FakeCRM(seed=SEED, state=tmp_path / "s.json"))
    by = {r["id"]: r for r in out["results"]}
    assert by["L-019"]["status"] == "disqualified" and by["L-019"]["crm"] is None      # competitor never written
    assert by["L-027"]["crm"] is None                                                  # junk never written
    assert by["L-010"]["route"]["owner"] == "luka" and by["L-010"]["draft"] is None    # customer: account owner, no sales email
    assert by["L-007"]["status"] == by["L-016"]["status"] == "needs_edit"              # invented number, discount
    assert by["L-024"]["route"]["owner"] == by["L-003"]["route"]["owner"]              # same company, same owner
    assert by["L-020"]["status"] == "queued"
    recorded = json.loads((ROOT / "recordings" / "drafts.json").read_text())
    assert all(by[k]["draft"] == v for k, v in recorded.items())
