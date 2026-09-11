# tests/test_rules/test_m3_rules.py
import pytest
from src.token import Token

PossessiveRule = pytest.importorskip(
    "src.rules.m3.possessive_rule"
).PossessiveRule


class TestPossessiveRule:
    def test_my_becomes_m3(self, basic_context):
        tokens = [Token('my', 'm1', index=0)]
        rule = PossessiveRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[0].label == 'm3'

    def test_their_becomes_m3(self, basic_context):
        tokens = [Token('their', '', index=0)]
        rule = PossessiveRule()
        rule.apply(tokens, basic_context)
        assert tokens[0].label == 'm3'

    def test_regular_word_unchanged(self, basic_context):
        tokens = [Token('hello', '', index=0)]
        rule = PossessiveRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is False
        assert tokens[0].label == ''
