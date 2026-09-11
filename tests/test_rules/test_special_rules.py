# tests/test_rules/test_special_rules.py
import pytest
from src.ht_token import Token

MuchRule = pytest.importorskip("src.rules.special.much_rule", reason="rule not yet implemented")

pytestmark = pytest.mark.skipif(True, reason="special rules not fully implemented yet")


def test_placeholder():
    t = Token("much")
    assert t.word == "much"
