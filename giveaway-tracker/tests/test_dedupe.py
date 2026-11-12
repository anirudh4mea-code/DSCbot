import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import state as state_mod  # noqa: E402
import tracker  # noqa: E402

CONFIG = tracker.load_config(os.path.join(ROOT, "config.json"))
FIXTURE = os.path.join(HERE, "fixtures", "messages.json")


def run_once(state_path):
    data = state_mod.load(state_path)
    alerts = tracker.collect_alerts(tracker.fetch_fixture(FIXTURE), CONFIG, data, "123")
    state_mod.save(state_path, data, 5000)
    return alerts


def test_crosspost_deduped_and_noise_filtered(tmp_path):
    alerts = run_once(str(tmp_path / "seen.json"))
    ids = [a["id"] for a in alerts]
    # 1001 kept, 1002 is noise, 2001 is the same giveaway reposted, 2002 is new
    assert ids == ["1001", "2002"]
    assert alerts[0]["link"] == "https://discord.com/channels/500/501/7001"
    assert alerts[1]["deadline"] == "<t:1763500000:F>"
    assert "FundingPips" in alerts[1]["firms"]


def test_second_run_sends_nothing(tmp_path):
    path = str(tmp_path / "seen.json")
    assert len(run_once(path)) == 2
    assert run_once(path) == []
    saved = json.load(open(path))
    assert set(saved["seen_ids"]) == {"1001", "2002"}


def test_main_dry_run_does_not_write_state(tmp_path):
    path = tmp_path / "seen.json"
    assert tracker.main(["--dry-run", "--fixture", FIXTURE, "--state", str(path)]) == 0
    assert not path.exists()
