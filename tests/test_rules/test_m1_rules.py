# tests/test_rules/test_m1_rules.py
import pytest
from src.ht_token import Token

SomeNumberRule = pytest.importorskip(
    "src.rules.np.m1.some_number_rule", reason="rule not yet implemented"
)

pytestmark = pytest.mark.skipif(False, reason="")


def test_some_number_rule_exists():
    from src.rules.np.m1.some_number_rule import SomeNumberRule as R
    r = R()
    assert r.target_label == "m1"
    assert r.name == "some_number"
