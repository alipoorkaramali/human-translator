# tests/test_rules/test_m1_rules.py
from src.ht_token import Token
from src.core.context import Context
from src.rules.np.m1.some_number_rule import SomeNumberRule


def _ctx(**kwargs):
    c = Context()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def test_some_plus_number_becomes_adv():
    tokens = [
        Token("some", "m1", "", index=0),
        Token("5", "m1", "cardinal", index=1),
        Token("books", "", "", index=2),
    ]
    rule = SomeNumberRule()
    changed = rule.apply(tokens, _ctx())
    assert changed is True
    assert tokens[0].label == "adv"


def test_some_hundreds_stays():
    tokens = [
        Token("some", "m1", "", index=0),
        Token("hundreds", "m1", "cardinal", index=1),
        Token("of", "", "", index=2),
        Token("people", "", "", index=3),
    ]
    rule = SomeNumberRule()
    changed = rule.apply(tokens, _ctx())
    # نباید adv شود
    assert tokens[0].label != "adv"
    assert changed is False


def test_some_thousand_prefix_stays():
    tokens = [
        Token("some", "m1", "", index=0),
        Token("thousand", "m1", "cardinal", index=1),
        Token("soldiers", "", "", index=2),
    ]
    rule = SomeNumberRule()
    rule.apply(tokens, _ctx())
    assert tokens[0].label != "adv"


def test_compound_set_exception():
    tokens = [
        Token("some", "m1", "", index=0),
        Token("dozen", "m1", "cardinal", index=1),
        Token("eggs", "", "", index=2),
    ]
    ctx = _ctx(compound_set={"some dozen"})
    rule = SomeNumberRule()
    rule.apply(tokens, ctx)
    assert tokens[0].label != "adv"


def test_already_adv_skipped():
    tokens = [
        Token("some", "adv", "", index=0),
        Token("3", "m1", "cardinal", index=1),
    ]
    rule = SomeNumberRule()
    assert rule.apply(tokens, _ctx()) is False
