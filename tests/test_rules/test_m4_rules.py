# tests/test_rules/test_m4_rules.py
import pytest
from src.ht_token import Token

NumberAfterNounRule = pytest.importorskip(
    "src.rules.m4.number_after_noun", reason="rule not yet implemented"
)

pytestmark = pytest.mark.skipif(True, reason="m4 rules not fully implemented yet")


def test_placeholder():
    t = Token("5")
    assert t.word == "5"
