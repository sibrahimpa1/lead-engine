"""Group raw lead rows into people, merge each group into one record and explain why."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from . import normalize as N

FIELDS = ["first_name", "last_name", "company", "title", "country", "phone", "page", "message"]
INTENT_RANK = {"demo": 3, "pricing": 2, "webinar": 1, "blog": 0, "": 0}


@dataclass
class Lead:
    key: str                       # canonical email
    rows: list                     # raw rows, oldest first
    fields: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.rows[0]["id"]

    @property
    def merged_ids(self) -> list:
        return [r["id"] for r in self.rows]

    @property
    def domain(self) -> str:
        return N.domain(self.key)


def load_rows(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group(rows: list) -> list:
    """Two rows are the same person when their canonical emails match, or when the email
    domain and the folded full name match (one row typed the address differently)."""
    by_email: dict = {}
    order: list = []
    name_index: dict = {}
    for row in sorted(rows, key=lambda r: r["created_at"]):
        key = N.email(row["email"])
        name_key = (N.domain(row["email"]), N.person(row["first_name"], row["last_name"]))
        why = None
        if key in by_email:
            why = "same email after normalisation"
        elif name_key in name_index and name_key[0] and name_key[0] not in N.FREEMAIL:
            key = name_index[name_key]
            why = "same company domain and same name"
        if why:
            lead = by_email[key]
            lead.rows.append(row)
            raw = row["email"]
            lead.reasons.append(f"{row['id']} merged into {lead.id}: {why} ({raw.strip()!r} -> {key})")
        else:
            lead = Lead(key=key, rows=[row])
            by_email[key] = lead
            order.append(key)
            name_index.setdefault(name_key, key)
    leads = [by_email[k] for k in order]
    for lead in leads:
        lead.fields = merge(lead.rows)
    return leads


def merge(rows: list) -> dict:
    """Newest non-empty value wins for each field, except intent (strongest page wins) and
    message (all messages kept). Names keep their original capitalisation from the
    longest version, so 'anna' never replaces 'Anna'."""
    out: dict = {}
    for f in FIELDS:
        vals = [r[f].strip() for r in rows if r.get(f, "").strip()]
        if not vals:
            out[f] = ""
        elif f in ("first_name", "last_name"):
            out[f] = max(vals, key=lambda v: (sum(c.isupper() for c in v), len(v)))
        elif f == "page":
            out[f] = max(vals, key=lambda v: INTENT_RANK.get(v, 0))
        elif f == "message":
            out[f] = " / ".join(dict.fromkeys(vals))
        elif f == "company":
            out[f] = max(vals, key=len)
        else:
            out[f] = vals[-1]
    out["email"] = N.email(rows[-1]["email"])
    out["phone"] = N.phone(out["phone"], out["country"])
    out["sources"] = sorted({r["source"] for r in rows})
    out["first_seen"] = rows[0]["created_at"]
    return out
