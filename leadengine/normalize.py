"""Normalisation that deduplication depends on. Pure functions, no I/O."""
from __future__ import annotations

import re
import unicodedata

FREEMAIL = {"gmail.com", "googlemail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
            "aol.com", "proton.me", "protonmail.com", "gmx.de", "web.de", "mail.com"}
DOTLESS = {"gmail.com", "googlemail.com"}          # providers that ignore dots in the local part
COMPANY_SUFFIX = re.compile(r"[,.]?\s+(inc|ltd|llc|gmbh|bv|ab|sa|plc|co|corp|limited|& co)\.?$", re.I)
JUNK_WORDS = {"test", "asdf", "qwerty", "xxx", "aaa"}


def fold(text: str) -> str:
    """Lowercase, trim, and fold accents and umlauts so 'Krüger' and 'Krueger' compare equal."""
    text = (text or "").strip().lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def email(raw: str) -> str:
    """Canonical email: trimmed, lowercased, +tags removed, Gmail dots removed."""
    e = (raw or "").strip().lower()
    if "@" not in e:
        return ""
    local, domain = e.rsplit("@", 1)
    local = local.split("+", 1)[0]
    if domain in DOTLESS:
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def domain(raw_email: str) -> str:
    e = email(raw_email)
    return e.rsplit("@", 1)[1] if e else ""


def is_freemail(raw_email: str) -> bool:
    return domain(raw_email) in FREEMAIL


def company(name: str) -> str:
    n = (name or "").strip()
    while True:
        m = COMPANY_SUFFIX.search(n)
        if not m:
            break
        n = n[:m.start()].strip()
    return fold(n)


def person(first: str, last: str) -> str:
    return re.sub(r"\s+", " ", f"{fold(first)} {fold(last)}").strip()


def phone(raw: str, country: str = "") -> str:
    """E.164-style: '+' and digits. US numbers written as (415) 555-0144 get +1."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        return "+" + digits
    if country == "US" and len(digits) == 10:
        return "+1" + digits
    return digits


def looks_like_junk(first: str, last: str, raw_email: str, company_name: str) -> bool:
    words = {fold(first), fold(last), fold(company_name), email(raw_email).split("@")[0]}
    return bool(words & JUNK_WORDS) or domain(raw_email) in {"test.com", "example.com"}
