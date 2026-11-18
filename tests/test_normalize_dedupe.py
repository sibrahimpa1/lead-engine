from conftest import ROOT
from leadengine import normalize as N
from leadengine.dedupe import group, load_rows

ROWS = load_rows(ROOT / "data" / "leads.csv")


def test_email_canonical_form():
    assert N.email(" Anna.Krueger@Brightlane.example ") == "anna.krueger@brightlane.example"
    assert N.email("priyanka.rao+events@orbitcrate.example") == "priyanka.rao@orbitcrate.example"
    assert N.email("J.Doe+x@googlemail.com") == "jdoe@gmail.com"
    assert N.email("no-at-sign") == ""


def test_folding_and_company_names():
    assert N.person("anna", "Krüger") == N.person("Anna", "Krueger")
    assert N.company("OrbitCrate Inc.") == N.company("orbitcrate") == "orbitcrate"
    assert N.company("Brightlane Logistics GmbH") == "brightlane logistics"


def test_phone():
    assert N.phone("(415) 555-0144", "US") == "+14155550144"
    assert N.phone("+44 20 7946 0123", "GB") == "+442079460123"


def test_junk_and_freemail():
    assert N.looks_like_junk("Test", "Test", "test@test.com", "test")
    assert not N.looks_like_junk("Anna", "Krueger", "anna@brightlane.example", "Brightlane")
    assert N.is_freemail("sam.okafor@gmail.com") and not N.is_freemail("tom@tallyfold.example")


def test_duplicates_are_merged_with_reasons():
    people = {p.id: p for p in group(ROWS)}
    assert people["L-001"].merged_ids == ["L-001", "L-002"]       # case, spaces, webinar re-entry
    assert people["L-004"].merged_ids == ["L-004", "L-005"]       # +tag and caps
    assert people["L-021"].merged_ids == ["L-021", "L-022"]       # double submit
    assert all("merged into" in r for p in people.values() for r in p.reasons)
    assert len(people) == len(ROWS) - 3


def test_colleagues_are_not_merged():
    ids = {p.id for p in group(ROWS)}
    assert {"L-003", "L-024"} <= ids          # same company, different people


def test_merge_keeps_best_values():
    lead = {p.id: p for p in group(ROWS)}["L-001"]
    f = lead.fields
    assert (f["first_name"], f["last_name"]) == ("Anna", "Krüger")
    assert f["page"] == "pricing" and f["phone"] == "+493012345601"
    assert f["sources"] == ["webform", "webinar"] and f["company"] == "Brightlane Logistics"
