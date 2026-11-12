"""Decide whether a Discord message looks like a prop-firm giveaway."""
import hashlib
import re

URL_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"<[@#:&!a-zA-Z0-9_]+>")
NON_WORD_RE = re.compile(r"[^a-z0-9% ]+")
SPACE_RE = re.compile(r"\s+")
DEADLINE_RE = re.compile(
    r"(?:ends?|ending|deadline|closes?|until|winners? (?:announced|drawn|picked))"
    r"[^\n.]{0,60}",
    re.IGNORECASE,
)
DISCORD_TS_RE = re.compile(r"<t:(\d+)(?::[a-zA-Z])?>")


def message_text(msg):
    """All human-readable text in a message: content plus embed text."""
    parts = [msg.get("content") or ""]
    for e in msg.get("embeds") or []:
        parts.append(e.get("title") or "")
        parts.append(e.get("description") or "")
        for f in e.get("fields") or []:
            parts.append(f.get("name") or "")
            parts.append(f.get("value") or "")
    return "\n".join(p for p in parts if p).strip()


def score(text, config):
    """Return (score, matched_firms) for the given text."""
    low = text.lower()
    total = 0
    for kw, weight in config["giveaway_keywords"].items():
        if kw.lower() in low:
            total += weight
    firms = []
    for firm in config["prop_firms"]:
        pattern = r"(?<![a-z0-9])" + re.escape(firm.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, low):
            firms.append(firm)
    if firms:
        total += config.get("prop_firm_weight", 1)
    return total, firms


def is_giveaway(text, config, include_all=False):
    if not text:
        return False, []
    s, firms = score(text, config)
    if include_all:
        return True, firms
    return s >= config["score_threshold"], firms


def normalize(text):
    t = text.lower()
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    t = NON_WORD_RE.sub(" ", t)
    t = SPACE_RE.sub(" ", t).strip()
    return t[:300]


def content_hash(text):
    return hashlib.sha256(normalize(text).encode()).hexdigest()[:24]


def find_deadline(text):
    ts = DISCORD_TS_RE.search(text)
    if ts:
        return f"<t:{ts.group(1)}:F>"
    m = DEADLINE_RE.search(text)
    return m.group(0).strip() if m else None
