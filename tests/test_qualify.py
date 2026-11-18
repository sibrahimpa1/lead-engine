from leadengine.qualify import Router, load_icp, score

ICP = load_icp()
BASE = {"first_name": "A", "last_name": "B", "email": "a@x.example", "company": "X", "title": "VP Sales",
        "country": "GB", "page": "demo", "message": ""}
ENRICH = {"industry": {"value": "saas"}, "employees": {"value": 300}, "tech": {"value": ["hubspot"]}}


def test_score_is_the_sum_of_its_reasons():
    s = score(BASE, ENRICH, ICP, None)
    assert s["score"] == min(100, sum(p["points"] for p in s["parts"]))
    labels = [p["label"] for p in s["parts"]]
    assert "industry: saas" in labels and "intent: visited demo" in labels and s["hot"]


def test_disqualifiers():
    assert score({**BASE, "email": "x@leadforge.example"}, ENRICH, ICP, None)["disqualified"] == ["competitor domain"]
    assert score({**BASE, "title": "student"}, {}, ICP, None)["disqualified"]
    assert score(BASE, ENRICH, ICP, {"lifecycle": "customer"})["disqualified"][0].startswith("already a customer")
    assert score({**BASE, "first_name": "Test", "email": "test@test.com"}, {}, ICP, None)["disqualified"]


def test_freemail_and_unknown_company_lose_points():
    s = score({**BASE, "email": "a@gmail.com"}, {}, ICP, None)
    assert {"personal email address", "company not found in enrichment data"} <= {p["label"] for p in s["parts"]}


def test_routing_rules():
    r = Router(ICP)
    hot = {"score": 90, "qualified": True, "hot": True}
    warm = {"score": 60, "qualified": True, "hot": False}
    assert r.route(BASE, warm, "amira")["owner"] == "amira"
    assert r.route(BASE, hot, None, "a.example")["owner"] == "mateo"
    assert r.route(BASE, warm, None, "a.example")["reason"].startswith("same company")
    assert r.route(BASE, {"score": 10, "qualified": False, "hot": False}, None)["owner"] is None


def test_capacity_queue_and_determinism():
    owners = []
    for _ in range(2):
        r = Router(ICP)
        owners.append([r.route({**BASE, "country": "DE"}, {"score": 60, "qualified": True, "hot": False}, None, f"d{i}.example")["owner"]
                       for i in range(10)])
    assert owners[0] == owners[1]
    assert owners[0].count(None) == 2 and owners[0].count("amira") == 4 and owners[0].count("luka") == 4


def test_no_rep_in_territory_uses_fallback():
    r = Router(ICP)
    assert r.route({**BASE, "country": "AU"}, {"score": 60, "qualified": True, "hot": False}, None)["owner"] == "mateo"
