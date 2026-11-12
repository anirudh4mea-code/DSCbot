"""Read messages from the hub server's channels with a Discord bot token."""
import time

import requests

API = "https://discord.com/api/v10"
DISCORD_EPOCH_MS = 1420070400000
# Channel types: 0 text, 5 announcement, 15 forum is skipped (needs thread reads)
READABLE_TYPES = {0, 5}


def snowflake_from_time(unix_seconds):
    return str((int(unix_seconds * 1000) - DISCORD_EPOCH_MS) << 22)


class DiscordClient:
    def __init__(self, token, session=None):
        self.s = session or requests.Session()
        self.s.headers.update({
            "Authorization": f"Bot {token}",
            "User-Agent": "DiscordBot (giveaway-tracker, 1.0)",
        })

    def _get(self, path, params=None):
        for _ in range(5):
            r = self.s.get(API + path, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.25)
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Rate limited too many times on {path}")

    def guild_channels(self, guild_id):
        chans = self._get(f"/guilds/{guild_id}/channels")
        return [c for c in chans if c.get("type") in READABLE_TYPES]

    def channel(self, channel_id):
        return self._get(f"/channels/{channel_id}")

    def messages_after(self, channel_id, after_id):
        """All messages newer than after_id, oldest first."""
        out = []
        cursor = after_id
        while True:
            batch = self._get(
                f"/channels/{channel_id}/messages",
                {"after": cursor, "limit": 100},
            )
            if not batch:
                break
            batch.sort(key=lambda m: int(m["id"]))
            out.extend(batch)
            cursor = batch[-1]["id"]
            if len(batch) < 100:
                break
        return out


def source_label(msg, channel_name):
    """Crossposted (followed) messages are posted by a webhook named after the source."""
    author = msg.get("author") or {}
    name = author.get("global_name") or author.get("username") or "unknown"
    if msg.get("webhook_id"):
        return name  # e.g. "FTMO Community #giveaways"
    return f"{name} in #{channel_name}"


def jump_link(msg, hub_guild_id, channel_id):
    ref = msg.get("message_reference") or {}
    if ref.get("guild_id") and ref.get("channel_id") and ref.get("message_id"):
        return (f"https://discord.com/channels/{ref['guild_id']}/"
                f"{ref['channel_id']}/{ref['message_id']}")
    return f"https://discord.com/channels/{hub_guild_id}/{channel_id}/{msg['id']}"
