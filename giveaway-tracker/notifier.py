"""Send alerts to a Discord channel through a webhook."""
import time

import requests

MAX_EMBEDS = 10
COLOR = 0x2ECC71


def build_embed(alert):
    desc = alert["text"]
    if len(desc) > 900:
        desc = desc[:900].rstrip() + "…"
    fields = [{"name": "Source", "value": alert["source"][:1024], "inline": True}]
    if alert.get("firms"):
        fields.append({"name": "Prop firm", "value": ", ".join(alert["firms"])[:1024],
                       "inline": True})
    if alert.get("deadline"):
        fields.append({"name": "Deadline", "value": alert["deadline"][:1024], "inline": False})
    fields.append({"name": "Link", "value": f"[Open original]({alert['link']})", "inline": False})
    return {
        "title": "🎁 New prop firm giveaway",
        "description": desc or "(no text — check the link)",
        "color": COLOR,
        "fields": fields,
        "timestamp": alert.get("timestamp"),
    }


def build_payloads(alerts, run_label):
    payloads = []
    for i in range(0, len(alerts), MAX_EMBEDS):
        chunk = alerts[i:i + MAX_EMBEDS]
        payload = {
            "username": "Giveaway Tracker",
            "embeds": [build_embed(a) for a in chunk],
            "allowed_mentions": {"parse": []},
        }
        if i == 0:
            payload["content"] = f"**{len(alerts)} new giveaway(s)** — {run_label}"
        payloads.append(payload)
    return payloads


def send(webhook_url, payloads):
    for p in payloads:
        for _ in range(5):
            r = requests.post(webhook_url, json=p, timeout=30)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.25)
                continue
            r.raise_for_status()
            break


def send_text(webhook_url, text):
    send(webhook_url, [{"username": "Giveaway Tracker", "content": text,
                        "allowed_mentions": {"parse": []}}])
