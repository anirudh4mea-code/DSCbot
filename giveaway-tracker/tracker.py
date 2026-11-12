"""Check the hub Discord server for new prop-firm giveaways and alert once per giveaway.

Usage:
  python tracker.py                 # real run (needs env vars below)
  python tracker.py --dry-run       # print alerts, don't send or save state
  python tracker.py --dry-run --fixture tests/fixtures/messages.json

Env vars: DISCORD_BOT_TOKEN, DISCORD_HUB_GUILD_ID, DISCORD_ALERT_WEBHOOK_URL
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import filters  # noqa: E402
import notifier  # noqa: E402
import state as state_mod  # noqa: E402
from discord_source import (DiscordClient, jump_link, snowflake_from_time,  # noqa: E402
                            source_label)

IST = timezone(timedelta(hours=5, minutes=30))


def load_config(path):
    with open(path) as f:
        return json.load(f)


def collect_alerts(channel_messages, config, data, hub_guild_id):
    """channel_messages: list of (channel_id, channel_name, [messages oldest first])."""
    dedupe = state_mod.Deduper(data)
    include_all = set(map(str, config.get("include_all_channels", [])))
    alerts = []
    for channel_id, channel_name, msgs in channel_messages:
        for msg in msgs:
            text = filters.message_text(msg)
            ok, firms = filters.is_giveaway(text, config, channel_id in include_all)
            if not ok:
                continue
            h = filters.content_hash(text)
            if not dedupe.is_new(msg["id"], h):
                continue
            dedupe.mark(msg["id"], h)
            alerts.append({
                "id": msg["id"],
                "text": text,
                "firms": firms,
                "deadline": filters.find_deadline(text),
                "source": source_label(msg, channel_name),
                "link": jump_link(msg, hub_guild_id, channel_id),
                "timestamp": msg.get("timestamp"),
            })
    return alerts


def fetch_live(config, data, token, guild_id):
    client = DiscordClient(token)
    if config.get("channels"):
        chans = [client.channel(str(c)) for c in config["channels"]]
    else:
        chans = client.guild_channels(guild_id)
    lookback = time.time() - config.get("first_run_lookback_hours", 24) * 3600
    result = []
    for c in chans:
        cid = str(c["id"])
        after = data["last_message_id"].get(cid) or snowflake_from_time(lookback)
        try:
            msgs = client.messages_after(cid, after)
        except Exception as e:  # missing permission on one channel shouldn't kill the run
            print(f"warn: could not read #{c.get('name')} ({cid}): {e}", file=sys.stderr)
            continue
        if msgs:
            data["last_message_id"][cid] = msgs[-1]["id"]
        result.append((cid, c.get("name", cid), msgs))
    return result


def fetch_fixture(path):
    with open(path) as f:
        raw = json.load(f)
    return [(str(c["channel_id"]), c["channel_name"], c["messages"]) for c in raw]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "config.json"))
    ap.add_argument("--state", default=os.path.join(HERE, "state", "seen.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args(argv)

    config = load_config(args.config)
    data = state_mod.load(args.state)
    guild_id = os.environ.get("DISCORD_HUB_GUILD_ID", "0")

    if args.fixture:
        channel_messages = fetch_fixture(args.fixture)
    else:
        token = os.environ.get("DISCORD_BOT_TOKEN")
        if not token or guild_id == "0":
            sys.exit("DISCORD_BOT_TOKEN and DISCORD_HUB_GUILD_ID must be set")
        channel_messages = fetch_live(config, data, token, guild_id)

    alerts = collect_alerts(channel_messages, config, data, guild_id)
    run_label = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    print(f"{len(alerts)} new giveaway(s) found")

    if args.dry_run:
        for a in alerts:
            print("-" * 60)
            print(f"[{a['source']}] firms={a['firms']} deadline={a['deadline']}")
            print(a["text"][:300])
            print(a["link"])
        return 0

    webhook = os.environ.get("DISCORD_ALERT_WEBHOOK_URL")
    if not webhook:
        sys.exit("DISCORD_ALERT_WEBHOOK_URL must be set")
    if alerts:
        notifier.send(webhook, notifier.build_payloads(alerts, run_label))
    elif config.get("send_empty_summary"):
        notifier.send_text(webhook, f"No new giveaways — {run_label}")

    # Save only after alerts are delivered, so a failed send is retried next run.
    state_mod.save(args.state, data, config.get("max_seen_entries", 5000))
    return 0


if __name__ == "__main__":
    sys.exit(main())
