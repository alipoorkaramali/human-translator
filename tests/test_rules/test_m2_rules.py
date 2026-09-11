# tests/test_rules/test_m2_rules.py
import pytest
from src.ht_token import Token

MoreMostRule = pytest.importorskip(
    "src.rules.m2.more_most_rule", reason="rule not yet implemented"
)

pytestmark = pytest.mark.skipif(True, reason="m2 rules not fully implemented yet")


def test_placeholder():
    t = Token("more")
    assert t.word == "more"
