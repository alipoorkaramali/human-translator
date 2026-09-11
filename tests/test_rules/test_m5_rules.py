# tests/test_rules/test_m5_rules.py
import pytest
from src.ht_token import Token

FallbackRule = pytest.importorskip(
    "src.rules.m5.fallback_rule", reason="rule not yet implemented"
)

pytestmark = pytest.mark.skipif(True, reason="m5 rules not fully implemented yet")


def test_placeholder():
    t = Token("x")
    assert t.word == "x"
