# tests/test_rules/test_m5_rules.py
import pytest
from src.token import Token

FallbackRule = pytest.importorskip(
    "src.rules.m5.fallback_rule"
).FallbackRule


class TestFallbackRule:
    def test_m5_becomes_adv(self, basic_context):
        tokens = [Token('word', 'm5', index=0)]
        rule = FallbackRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[0].label == 'adv'

    def test_non_m5_unchanged(self, basic_context):
        tokens = [Token('word', 'N', index=0)]
        rule = FallbackRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is False
