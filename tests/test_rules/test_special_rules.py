# tests/test_rules/test_special_rules.py
import pytest
from src.token import Token

MuchRule = pytest.importorskip("src.rules.special.much_rule").MuchRule


class TestMuchRule:
    def test_much_before_adj_becomes_adv(self, basic_context):
        tokens = [
            Token('much', 'm1', index=0),
            Token('better', 'm2', index=1),
        ]
        rule = MuchRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[0].label == 'adv'

    def test_much_before_adv_becomes_adv(self, basic_context):
        tokens = [
            Token('much', 'm1', index=0),
            Token('quickly', 'adv', index=1),
        ]
        rule = MuchRule()
        rule.apply(tokens, basic_context)
        assert tokens[0].label == 'adv'
