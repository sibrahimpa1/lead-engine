"""CRM writes that are safe to repeat.

FakeCRM is a HubSpot-shaped store used by the demo and the tests. HubSpotCRM talks to the
real CRM v3 API with a private-app token; it is optional and not run in CI. Both upsert by
email and only send fields that changed, so running the same batch twice writes nothing.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

PROPS = ["email", "firstname", "lastname", "jobtitle", "company", "country", "phone", "lead_score", "owner", "lead_source"]
PROTECTED = {"owner", "lifecycle"}       # never overwritten on an existing contact


class FakeCRM:
    def __init__(self, seed: Path | None = None, state: Path | None = None):
        self.state = state
        if state and state.exists():
            data = json.loads(state.read_text())
        else:
            data = json.loads(seed.read_text()) if seed else {"contacts": [], "companies": []}
        self.contacts = {c["email"]: c for c in data["contacts"]}
        self.companies = {c["domain"]: c for c in data["companies"]}
        self.log: list = []

    def find_contact(self, email: str) -> dict | None:
        return self.contacts.get(email)

    def find_company(self, domain: str) -> dict | None:
        return self.companies.get(domain)

    def upsert_contact(self, props: dict) -> dict:
        email = props["email"]
        current = self.contacts.get(email)
        if current is None:
            cid = f"C-{9100 + len(self.contacts)}"
            self.contacts[email] = {"id": cid, **props}
            op = {"op": "create", "id": cid, "email": email, "fields": sorted(props)}
        else:
            changes = {k: v for k, v in props.items()
                       if v not in ("", None) and current.get(k) != v
                       and not (k in PROTECTED and current.get(k))}
            if not changes:
                op = {"op": "noop", "id": current["id"], "email": email, "fields": []}
            else:
                current.update(changes)
                op = {"op": "update", "id": current["id"], "email": email, "fields": sorted(changes)}
        self.log.append(op)
        return op

    def save(self) -> None:
        if self.state:
            self.state.parent.mkdir(parents=True, exist_ok=True)
            self.state.write_text(json.dumps({"contacts": list(self.contacts.values()),
                                              "companies": list(self.companies.values())}, indent=1))


class HubSpotCRM:
    """Real HubSpot through the CRM v3 objects API (search, create, patch).
    Needs HUBSPOT_TOKEN from a private app with crm.objects.contacts read/write scopes."""

    BASE = "https://api.hubapi.com"

    def __init__(self, token: str | None = None):
        self.token = token or os.environ["HUBSPOT_TOKEN"]
        self.log: list = []

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(self.BASE + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"{}")

    def find_contact(self, email: str) -> dict | None:
        res = self._call("POST", "/crm/v3/objects/contacts/search", {
            "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
            "properties": PROPS, "limit": 1})
        hits = res.get("results", [])
        return {"id": hits[0]["id"], **hits[0]["properties"]} if hits else None

    def find_company(self, domain: str) -> dict | None:
        res = self._call("POST", "/crm/v3/objects/companies/search", {
            "filterGroups": [{"filters": [{"propertyName": "domain", "operator": "EQ", "value": domain}]}],
            "properties": ["domain", "name", "hubspot_owner_id"], "limit": 1})
        hits = res.get("results", [])
        return {"id": hits[0]["id"], **hits[0]["properties"]} if hits else None

    def upsert_contact(self, props: dict) -> dict:
        # custom properties (lead_score, owner, lead_source) must exist in the portal first
        current = self.find_contact(props["email"])
        if current is None:
            res = self._call("POST", "/crm/v3/objects/contacts", {"properties": props})
            op = {"op": "create", "id": res.get("id"), "email": props["email"], "fields": sorted(props)}
        else:
            changes = {k: v for k, v in props.items() if v not in ("", None) and current.get(k) != v
                       and not (k in PROTECTED and current.get(k))}
            if changes:
                self._call("PATCH", f"/crm/v3/objects/contacts/{current['id']}", {"properties": changes})
            op = {"op": "update" if changes else "noop", "id": current["id"], "email": props["email"], "fields": sorted(changes)}
        self.log.append(op)
        return op

    def save(self) -> None:
        pass
