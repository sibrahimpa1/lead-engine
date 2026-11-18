"""Generate the synthetic demo data. Every company, person and domain here is made up;
domains use the reserved .example TLD. Run: python data/make_synthetic.py"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent

COMPANIES = [
    # domain, name, industry, employees, country, tech
    ("brightlane.example", "Brightlane Logistics GmbH", "logistics", 420, "DE", ["hubspot", "shopware"]),
    ("tallyfold.example", "Tallyfold", "fintech", 180, "GB", ["salesforce", "stripe"]),
    ("orbitcrate.example", "OrbitCrate Inc.", "saas", 95, "US", ["hubspot", "segment"]),
    ("kestrelhealth.example", "Kestrel Health", "healthcare", 2600, "US", ["salesforce"]),
    ("fennick.example", "Fennick & Co", "agency", 12, "IE", ["hubspot"]),
    ("marrowsoft.example", "Marrowsoft Ltd", "saas", 640, "GB", ["hubspot", "intercom"]),
    ("quillpay.example", "QuillPay", "fintech", 60, "NL", ["stripe"]),
    ("dunmore.example", "Dunmore Freight", "logistics", 1300, "US", ["salesforce"]),
    ("lumenvale.example", "Lumenvale Studios", "media", 35, "FR", []),
    ("cobaltrail.example", "Cobalt Rail Systems", "manufacturing", 900, "DE", ["salesforce", "sap"]),
    ("pebbleworks.example", "Pebbleworks", "saas", 240, "US", ["hubspot"]),
    ("harborline.example", "Harborline Shipping", "logistics", 75, "NL", ["hubspot"]),
    ("sablemint.example", "Sablemint", "fintech", 410, "US", ["salesforce", "segment"]),
    ("verdantly.example", "Verdantly", "retail", 150, "ES", ["shopware"]),
    ("arcpipe.example", "ArcPipe Analytics", "saas", 55, "SE", ["hubspot"]),
    ("leadforge.example", "LeadForge", "saas", 300, "US", ["hubspot"]),           # a competitor
    ("ironbark.example", "Ironbark Insurance", "insurance", 3100, "AU", ["salesforce"]),
    ("glasswing.example", "Glasswing Payments", "fintech", 820, "GB", ["hubspot", "stripe"]),
]

L = [
    # id, created_at, source, first, last, email, company, title, country, phone, page, message
    ("L-001", "2026-11-16T08:02:00Z", "webform", "Anna", "Krüger", "anna.krueger@brightlane.example", "Brightlane Logistics", "Head of Operations", "DE", "+49 30 1234 5601", "pricing", "We route 4k parcels a day and want to automate carrier selection."),
    ("L-002", "2026-11-16T08:40:00Z", "webinar", "anna", "krüger", " Anna.Krueger@Brightlane.example ", "Brightlane", "Head of Ops", "DE", "", "webinar", ""),
    ("L-003", "2026-11-16T09:15:00Z", "webform", "Tom", "Ashby", "tom@tallyfold.example", "Tallyfold", "VP Revenue Operations", "GB", "+44 20 7946 0123", "demo", "Need a demo for the RevOps team this month."),
    ("L-004", "2026-11-16T09:20:00Z", "csv_import", "Priyanka", "Rao", "priyanka.rao+events@orbitcrate.example", "OrbitCrate", "Director of Growth", "US", "(415) 555-0144", "", "Met at SaaStock booth."),
    ("L-005", "2026-11-16T10:05:00Z", "webform", "Priyanka", "Rao", "PRIYANKA.RAO@orbitcrate.example", "OrbitCrate Inc", "Director, Growth", "US", "+1 415 555 0144", "pricing", ""),
    ("L-006", "2026-11-16T10:30:00Z", "chat", "Sam", "Okafor", "sam.okafor@gmail.com", "", "student", "NG", "", "blog", "Writing my thesis on CRMs, can I get a free account?"),
    ("L-007", "2026-11-16T11:00:00Z", "webform", "Dana", "Whitfield", "dana@kestrelhealth.example", "Kestrel Health", "CIO", "US", "+1 617 555 0190", "demo", "Evaluating vendors for Q1."),
    ("L-008", "2026-11-16T11:12:00Z", "webform", "Liam", "Fennick", "liam@fennick.example", "Fennick & Co", "Founder", "IE", "", "pricing", "Small agency, 12 people."),
    ("L-009", "2026-11-16T12:01:00Z", "csv_import", "Grace", "Lin", "grace.lin@marrowsoft.example", "Marrowsoft", "Head of Sales Operations", "GB", "+44 161 555 0177", "", ""),
    ("L-010", "2026-11-16T12:30:00Z", "webform", "Ruud", "Visser", "ruud@quillpay.example", "QuillPay", "COO", "NL", "+31 20 555 0110", "pricing", "Payments startup, growing fast."),
    ("L-011", "2026-11-16T13:00:00Z", "webinar", "Marcus", "Bell", "m.bell@dunmore.example", "Dunmore Freight", "Director of Operations", "US", "", "webinar", ""),
    ("L-012", "2026-11-16T13:45:00Z", "webform", "Chloé", "Martin", "chloe@lumenvale.example", "Lumenvale Studios", "Producer", "FR", "", "blog", "Just browsing."),
    ("L-013", "2026-11-16T14:10:00Z", "csv_import", "Jonas", "Weber", "jonas.weber@cobaltrail.example", "Cobalt Rail", "Head of IT", "DE", "+49 89 555 0133", "", ""),
    ("L-014", "2026-11-16T14:20:00Z", "webform", "Ella", "Moreno", "ella.moreno@pebbleworks.example", "Pebbleworks", "VP Customer Success", "US", "+1 512 555 0188", "demo", "Our CS team needs routing by account tier."),
    ("L-015", "2026-11-16T15:00:00Z", "webform", "Pieter", "de Boer", "pieter@harborline.example", "Harborline Shipping", "Operations Manager", "NL", "", "pricing", ""),
    ("L-016", "2026-11-16T15:30:00Z", "chat", "Noah", "Kim", "noah.kim@sablemint.example", "Sablemint", "Chief Revenue Officer", "US", "+1 646 555 0101", "pricing", "Can you integrate with Salesforce?"),
    ("L-017", "2026-11-16T16:00:00Z", "webform", "Lucía", "Fernández", "lucia@verdantly.example", "Verdantly", "Marketing Manager", "ES", "", "blog", ""),
    ("L-018", "2026-11-16T16:20:00Z", "webform", "Erik", "Lund", "erik.lund@arcpipe.example", "ArcPipe Analytics", "CEO", "SE", "+46 8 555 0150", "demo", "Want lead routing for our 3 SDRs."),
    ("L-019", "2026-11-16T16:45:00Z", "webform", "Blake", "Harper", "blake@leadforge.example", "LeadForge", "Product Manager", "US", "", "pricing", "Curious how your scoring works."),
    ("L-020", "2026-11-16T17:00:00Z", "csv_import", "Mia", "Thornton", "mia.thornton@ironbark.example", "Ironbark Insurance", "Head of Distribution", "AU", "+61 2 5550 1122", "", ""),
    ("L-021", "2026-11-16T17:30:00Z", "webform", "Oliver", "Grant", "oliver.grant@glasswing.example", "Glasswing Payments", "Head of Revenue Operations", "GB", "+44 20 5550 0199", "demo", "Replacing a manual lead process."),
    ("L-022", "2026-11-16T17:31:00Z", "webform", "Oliver", "Grant", "oliver.grant@glasswing.example", "Glasswing Payments", "Head of Revenue Operations", "GB", "+44 20 5550 0199", "demo", "Replacing a manual lead process."),
    ("L-023", "2026-11-16T18:00:00Z", "webform", "Hana", "Novak", "hana.novak@yahoo.com", "Novak Consulting", "Consultant", "CZ", "", "pricing", ""),
    ("L-024", "2026-11-16T18:15:00Z", "webinar", "Ben", "Carter", "ben.carter@tallyfold.example", "Tallyfold", "Sales Manager", "GB", "", "webinar", ""),
    ("L-025", "2026-11-16T18:40:00Z", "csv_import", "Sofia", "Ricci", "s.ricci@unknownco.example", "Unknown Co", "Office Manager", "IT", "", "", ""),
    ("L-026", "2026-11-16T19:00:00Z", "webform", "Jamal", "Reed", "jamal.reed@marrowsoft.example", "Marrowsoft", "VP Sales", "GB", "+44 161 555 0178", "pricing", "Want to compare plans."),
    ("L-027", "2026-11-16T19:10:00Z", "webform", "Test", "Test", "test@test.com", "test", "test", "", "", "", "asdf"),
    ("L-028", "2026-11-16T19:30:00Z", "webform", "Ingrid", "Berg", "ingrid.berg@arcpipe.example", "ArcPipe", "Head of Sales", "SE", "", "pricing", ""),
]

CRM = {
    "contacts": [
        {"id": "C-9001", "email": "grace.lin@marrowsoft.example", "firstname": "Grace", "lastname": "Lin",
         "jobtitle": "Sales Ops Lead", "company_domain": "marrowsoft.example", "owner": "amira", "lifecycle": "lead"},
        {"id": "C-9002", "email": "ruud@quillpay.example", "firstname": "Ruud", "lastname": "Visser",
         "jobtitle": "COO", "company_domain": "quillpay.example", "owner": "luka", "lifecycle": "customer"},
    ],
    "companies": [
        {"id": "CO-501", "domain": "marrowsoft.example", "name": "Marrowsoft Ltd", "owner": "amira"},
        {"id": "CO-502", "domain": "quillpay.example", "name": "QuillPay", "owner": "luka"},
    ],
}

HEAD = ["id", "created_at", "source", "first_name", "last_name", "email", "company", "title", "country", "phone", "page", "message"]


def main():
    with open(HERE / "leads.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEAD)
        w.writerows(L)
    firmo = {d: {"name": n, "industry": i, "employees": e, "country": c, "tech": t} for d, n, i, e, c, t in COMPANIES}
    (HERE / "firmographics.json").write_text(json.dumps(firmo, indent=1, ensure_ascii=False))
    (HERE / "crm_seed.json").write_text(json.dumps(CRM, indent=1))


if __name__ == "__main__":
    main()
