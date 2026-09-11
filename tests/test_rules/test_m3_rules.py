# tests/test_rules/test_m3_rules.py
import pytest
from src.ht_token import Token

PossessiveRule = pytest.importorskip(
    "src.rules.m3.possessive_rule", reason="rule not yet implemented"
)

pytestmark = pytest.mark.skipif(True, reason="m3 rules not fully implemented yet")


def test_placeholder():
    t = Token("his")
    assert t.word == "his"
