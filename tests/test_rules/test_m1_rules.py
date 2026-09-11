# tests/test_rules/test_m1_rules.py
import pytest
from src.token import Token

# skipif در سطح ماژول
SomeNumberRule = pytest.importorskip(
    "src.rules.m1.some_number_rule"
).SomeNumberRule


class TestSomeNumberRule:
    def test_some_five_becomes_adv(self, basic_context):
        tokens = [
            Token('some', 'm1', index=0),
            Token('five', 'm1', numtype='cardinal', index=1),
        ]
        rule = SomeNumberRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[0].label == 'adv'

    def test_some_hundreds_stays_m1(self, basic_context):
        tokens = [
            Token('some', 'm1', index=0),
            Token('hundreds', 'm1', index=1),
        ]
        rule = SomeNumberRule()
        rule.apply(tokens, basic_context)
        assert tokens[0].label == 'm1'

    def test_some_alone_unchanged(self, basic_context):
        tokens = [
            Token('some', 'm1', index=0),
            Token('books', 'N', index=1),
        ]
        rule = SomeNumberRule()
        rule.apply(tokens, basic_context)
        assert tokens[0].label == 'm1'

    def test_no_change_when_not_m1(self, basic_context):
        tokens = [
            Token('some', 'N', index=0),
            Token('five', 'm1', numtype='cardinal', index=1),
        ]
        rule = SomeNumberRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is False
