import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import filters  # noqa: E402

with open(os.path.join(os.path.dirname(HERE), "config.json")) as f:
    CONFIG = json.load(f)


def check(text):
    return filters.is_giveaway(text, CONFIG)[0]


def test_detects_giveaways():
    assert check("GIVEAWAY: 2x FTMO 100k challenges, react to enter!")
    assert check("We're giving away a free funded account to one lucky trader")
    assert check("Monthly raffle — win a free challenge from FundingPips")
    assert check("Chance to win a Topstep combine, winners picked Sunday")


def test_ignores_normal_posts():
    assert not check("Market update: NFP is out, expect volatility")
    assert not check("Server rules updated, please read #rules")
    assert not check("FTMO payout proof from one of our members")
    assert not check("")


def test_firm_matching_uses_word_boundaries():
    _, firms = filters.score("Apex giveaway", CONFIG)
    assert "Apex" in firms
    _, firms = filters.score("the apexes of the chart", CONFIG)
    assert "Apex" not in firms


def test_include_all_channel_passes_everything():
    assert filters.is_giveaway("anything at all", CONFIG, include_all=True)[0]


def test_hash_ignores_links_and_case():
    a = filters.content_hash("GIVEAWAY now! https://a.com/x")
    b = filters.content_hash("giveaway   now https://b.com/y")
    assert a == b


def test_deadline():
    assert filters.find_deadline("Ends <t:1763500000:R>") == "<t:1763500000:F>"
    assert filters.find_deadline("Giveaway ends Friday 8pm") == "ends Friday 8pm"
    assert filters.find_deadline("no date here") is None
