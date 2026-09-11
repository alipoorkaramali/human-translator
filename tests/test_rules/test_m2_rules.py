# tests/test_rules/test_m2_rules.py
import pytest
from src.ht_token import Token


def test_more_most_placeholder():
    from src.rules.np.m2.more_most_rule import MoreMostRule
    r = MoreMostRule()
    assert r.target_label == "m2"
