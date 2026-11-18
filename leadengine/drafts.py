"""First-touch email drafts: the model writes, code checks, a person approves, then it can send.

Checks run on every draft before it reaches the approval queue:
- greets the lead by first name and names their company;
- every number in the draft appears in what the lead told us (no invented facts);
- no promises the sales team can't make (discounts, guarantees, "free forever");
- no template leftovers like {first_name} or [Company];
- 120 words or fewer.
Sending is idempotent: the outbox key is the lead email plus a hash of the approved text.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from . import normalize as N

ROOT = Path(__file__).resolve().parent.parent
REPLAY = ROOT / "recordings" / "drafts.json"
BANNED = ["guarantee", "discount", "free forever", "risk-free", "no-brainer", "% off", "limited time"]
MAX_WORDS = 120

SYSTEM = """Write a first reply to an inbound B2B lead. Plain, friendly, under 100 words.
Use only facts from the lead record. Mention their company. Offer one concrete next step.
No discounts, guarantees or pricing numbers."""


class ReplayDrafter:
    name = "replay"

    def __init__(self, path: Path = REPLAY):
        self.records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def draft(self, lead: dict, context: dict) -> dict:
        rec = self.records.get(lead["id"])
        if rec:
            return dict(rec)
        first = lead["first_name"] or "there"
        return {"subject": f"Following up, {lead['company'] or 'your enquiry'}",
                "body": f"Hi {first},\n\nThanks for getting in touch. Would a short call next week help? "
                        f"I can walk you through how teams like {lead['company'] or 'yours'} set this up.\n\nBest,\n{context['owner_name']}"}


class ClaudeDrafter:
    """Live drafts with Claude (needs ANTHROPIC_API_KEY and the anthropic package)."""

    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("LLM_MODEL", "claude-opus-5-5")
        self.name = f"anthropic:{self.model}"

    def draft(self, lead: dict, context: dict) -> dict:
        facts = {k: lead[k] for k in ("first_name", "company", "title", "country", "page", "message")}
        response = self.client.beta.messages.create(
            model=self.model, max_tokens=16000, system=SYSTEM,
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": {
                "type": "object", "additionalProperties": False, "required": ["subject", "body"],
                "properties": {"subject": {"type": "string"}, "body": {"type": "string"}}}}},
            messages=[{"role": "user", "content": json.dumps({"lead": facts, "sender": context["owner_name"]})}])
        if response.stop_reason == "refusal":
            return {"subject": "", "body": ""}
        return json.loads(next(b.text for b in response.content if b.type == "text"))


def check(draft: dict, lead: dict) -> list:
    """Problems with a draft; an empty list means it can go to a person for approval."""
    body = draft.get("body", "")
    text = f"{draft.get('subject', '')}\n{body}"
    low = text.lower()
    problems = []
    if lead["first_name"] and lead["first_name"].lower() not in body.lower():
        problems.append("does not greet the lead by first name")
    core = N.company(lead["company"])            # 'Brightlane Logistics GmbH' -> 'brightlane logistics'
    if core and core not in N.fold(text) and core.split()[0] not in N.fold(text).split():
        problems.append(f"does not mention {lead['company']}")
    known = f"{lead['message']} {lead['title']} {lead['company']}"
    for num in re.findall(r"\d[\d,.]*k?", text):
        if num.rstrip(".,") not in known:
            problems.append(f"number {num.rstrip('.,')!r} is not in anything the lead told us")
    for word in BANNED:
        if word in low:
            problems.append(f"makes a promise sales can't make: {word!r}")
    if re.search(r"\{[^}]*\}|\[[A-Z][^\]]*\]", text):
        problems.append("has an unfilled template placeholder")
    words = len(body.split())
    if words > MAX_WORDS:
        problems.append(f"{words} words, limit is {MAX_WORDS}")
    return problems


def outbox_key(email: str, draft: dict) -> str:
    h = hashlib.sha256(f"{draft.get('subject','')}\n{draft.get('body','')}".encode()).hexdigest()[:12]
    return f"{email}:{h}"


class Approvals:
    """Approval state and outbox. Nothing is sent unless a person approved that exact text."""

    def __init__(self, state: Path | None = None):
        self.state = state
        data = json.loads(state.read_text()) if state and state.exists() else {"decisions": {}, "outbox": {}}
        self.decisions, self.outbox = data["decisions"], data["outbox"]

    def decide(self, lead_id: str, draft: dict, approved: bool, by: str, note: str = "") -> None:
        self.decisions[lead_id] = {"approved": approved, "by": by, "note": note, "key": outbox_key(lead_id, draft)}

    def send(self, lead_id: str, email: str, draft: dict) -> dict:
        d = self.decisions.get(lead_id)
        if not d or not d["approved"]:
            return {"sent": False, "reason": "not approved"}
        if d["key"] != outbox_key(lead_id, draft):
            return {"sent": False, "reason": "the text changed after approval"}
        key = outbox_key(email, draft)
        if key in self.outbox:
            return {"sent": False, "reason": "already sent (same lead, same text)", "key": key}
        self.outbox[key] = {"lead": lead_id, "to": email, "subject": draft["subject"]}
        return {"sent": True, "key": key}

    def save(self) -> None:
        if self.state:
            self.state.parent.mkdir(parents=True, exist_ok=True)
            self.state.write_text(json.dumps({"decisions": self.decisions, "outbox": self.outbox}, indent=1))
