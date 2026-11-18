"""Enrichment, scoring and routing. All of it is plain code with reasons, no model involved."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import normalize as N

ROOT = Path(__file__).resolve().parent.parent


def load_icp(path: Path = ROOT / "icp.json") -> dict:
    return json.loads(path.read_text())


class Firmographics:
    """Company data by domain. The demo reads a synthetic file; a real build would call an
    enrichment API behind the same method. Every value carries its source."""

    SOURCE = "firmographics.json (synthetic)"

    def __init__(self, path: Path = ROOT / "data" / "firmographics.json"):
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def lookup(self, domain: str) -> dict:
        rec = self.data.get(domain)
        if not rec:
            return {}
        return {k: {"value": v, "source": self.SOURCE} for k, v in rec.items()}


def _match(table: list, text: str) -> tuple:
    for pattern, pts in table:
        m = re.search(rf"\b({pattern})\b", text)
        if m:
            return m.group(1), pts
    return None, 0


def score(lead: dict, enrich: dict, icp: dict, crm_contact: dict | None) -> dict:
    """0-100 with one line per point source. Disqualifiers end scoring with a reason."""
    title = N.fold(lead["title"])
    email = lead["email"]
    disq = []
    if N.looks_like_junk(lead["first_name"], lead["last_name"], email, lead["company"]):
        disq.append("test or junk submission")
    if N.domain(email) in icp["competitors"]:
        disq.append("competitor domain")
    if "student" in title or "thesis" in N.fold(lead["message"]):
        disq.append("student or research request")
    if crm_contact and crm_contact.get("lifecycle") == "customer":
        disq.append("already a customer: sent to the account owner, not to new business")
    if disq:
        return {"score": 0, "qualified": False, "hot": False, "parts": [], "disqualified": disq}

    parts = []
    ind = enrich.get("industry", {}).get("value")
    if ind:
        parts.append((f"industry: {ind}", icp["industries"].get(ind, 0)))
    emp = enrich.get("employees", {}).get("value")
    if emp:
        pts = next(p for lo, hi, p in icp["employees"] if lo <= emp <= hi)
        parts.append((f"company size: {emp} employees", pts))
    country = lead["country"] or enrich.get("country", {}).get("value", "")
    if country:
        parts.append((f"country: {country}", icp["countries"].get(country, 0)))
    level, pts = _match(icp["seniority"], title)
    if level:
        parts.append((f"seniority: {level}", pts))
    func, pts = _match(icp["functions"], title)
    if func:
        parts.append((f"function: {func}", pts))
    for t in enrich.get("tech", {}).get("value", []):
        if t in icp["tech"]:
            parts.append((f"uses {t}", icp["tech"][t]))
    page = lead["page"]
    if icp["intent"].get(page, 0):
        parts.append((f"intent: visited {page}", icp["intent"][page]))
    if N.is_freemail(email):
        parts.append(("personal email address", -10))
    if not enrich:
        parts.append(("company not found in enrichment data", -5))
    total = max(0, min(100, sum(p for _, p in parts)))
    return {"score": total, "qualified": total >= icp["qualify_threshold"], "hot": total >= icp["hot_threshold"],
            "parts": [{"label": l, "points": p} for l, p in parts], "disqualified": []}


def territory(country: str, icp: dict) -> str:
    for name, countries in icp["routing"]["territories"].items():
        if country in countries:
            return name
    return ""


class Router:
    """Deterministic routing with capacity. Same input, same owner, every run."""

    def __init__(self, icp: dict):
        self.cfg = icp["routing"]
        self.load = {rep: 0 for rep in self.cfg["reps"]}
        self.accounts: dict = {}          # domain -> owner chosen earlier in this batch

    def _free(self, rep: str) -> bool:
        return self.load[rep] < self.cfg["reps"][rep]["capacity"]

    def _take(self, rep: str, reason: str) -> dict:
        self.load[rep] += 1
        return {"owner": rep, "owner_name": self.cfg["reps"][rep]["name"], "reason": reason}

    def route(self, lead: dict, result: dict, account_owner: str | None, domain: str = "") -> dict:
        out = self._route(lead, result, account_owner, domain)
        if domain and out["owner"] and domain not in self.accounts:
            self.accounts[domain] = out["owner"]
        return out

    def _route(self, lead: dict, result: dict, account_owner: str | None, domain: str) -> dict:
        if account_owner:
            return self._take(account_owner, "existing account: goes to the account owner") if account_owner in self.load \
                else {"owner": account_owner, "owner_name": account_owner, "reason": "existing account owner"}
        if not result["qualified"]:
            return {"owner": None, "owner_name": "", "reason": "not qualified: nurture list, no owner"}
        if domain in self.accounts:
            return self._take(self.accounts[domain], "same company as an earlier lead in this batch: same owner")
        senior = [r for r, v in self.cfg["reps"].items() if v.get("senior")]
        if result["hot"]:
            for rep in senior:
                if self._free(rep):
                    return self._take(rep, f"hot lead (score {result['score']}): senior rep")
        terr = territory(lead["country"], {"routing": self.cfg})
        reps = sorted((r for r, v in self.cfg["reps"].items() if v["territory"] == terr), key=lambda r: (self.load[r], r))
        for rep in reps:
            if self._free(rep):
                return self._take(rep, f"{terr} territory, lowest load")
        if not reps:
            fallback = self.cfg["unassigned_territory_owner"]
            if self._free(fallback):
                return self._take(fallback, f"no rep covers {terr or 'this country'}: fallback owner")
            return {"owner": None, "owner_name": "", "reason": f"no rep covers {terr or 'this country'} and the fallback owner is full: waiting in the queue"}
        return {"owner": None, "owner_name": "", "reason": f"every {terr} rep is at capacity: waiting in the queue"}
