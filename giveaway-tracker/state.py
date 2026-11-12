"""Persisted record of what has already been alerted, so nothing is sent twice."""
import json
import os


def load(path):
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("last_message_id", {})
    data.setdefault("seen_ids", [])
    data.setdefault("seen_hashes", [])
    return data


def save(path, data, max_entries):
    data["seen_ids"] = data["seen_ids"][-max_entries:]
    data["seen_hashes"] = data["seen_hashes"][-max_entries:]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


class Deduper:
    """Rejects messages already seen by ID or by near-identical content."""

    def __init__(self, data):
        self.data = data
        self.ids = set(data["seen_ids"])
        self.hashes = set(data["seen_hashes"])

    def is_new(self, msg_id, text_hash):
        return msg_id not in self.ids and text_hash not in self.hashes

    def mark(self, msg_id, text_hash):
        if msg_id not in self.ids:
            self.ids.add(msg_id)
            self.data["seen_ids"].append(msg_id)
        if text_hash not in self.hashes:
            self.hashes.add(text_hash)
            self.data["seen_hashes"].append(text_hash)
