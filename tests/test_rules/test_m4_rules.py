# tests/test_rules/test_m4_rules.py
import pytest
from src.token import Token

NumberAfterNounRule = pytest.importorskip(
    "src.rules.m4.number_after_noun_rule"
).NumberAfterNounRule


class TestNumberAfterNounRule:
    def test_number_after_noun_becomes_m4(self, basic_context):
        tokens = [
            Token('chapter', 'N', index=0),
            Token('five', 'm1', numtype='cardinal', index=1),
        ]
        rule = NumberAfterNounRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[1].label == 'm4'

    def test_number_after_of_stays_m1(self, basic_context):
        tokens = [
            Token('cell', 'N', index=0),
            Token('of', '', index=1),
            Token('one', 'm1', numtype='cardinal', index=2),
        ]
        rule = NumberAfterNounRule()
        rule.apply(tokens, basic_context)
        # عدد بعد از of باید m1 بماند
        assert tokens[2].label == 'm1'
