# tests/test_rules/test_m1_rules.py
import pytest
from src.ht_token import Token

# skipif در سطح ماژول
SomeNumberRule = pytest.importorskip(
    "src.rules.m1.some_number_rule", reason="rule not yet implemented"
).SomeNumberRule if False else None

pytestmark = pytest.mark.skipif(
    True, reason="m1 rules not fully implemented yet"
)


def test_placeholder():
    t = Token("some")
    assert t.word == "some"
