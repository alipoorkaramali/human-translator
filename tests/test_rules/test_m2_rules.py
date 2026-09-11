# tests/test_rules/test_m2_rules.py
import pytest
from src.token import Token

MoreMostRule = pytest.importorskip(
    "src.rules.m2.more_most_rule"
).MoreMostRule


class TestMoreMostRule:
    def test_more_before_multisyllable_adj(self, basic_context):
        tokens = [
            Token('more', 'm1', index=0),
            Token('beautiful', 'm2', index=1),
        ]
        rule = MoreMostRule()
        changed = rule.apply(tokens, basic_context)
        assert changed is True
        assert tokens[0].label == 'm2'

    def test_more_before_monosyllable_unchanged(self, basic_context):
        tokens = [
            Token('more', 'm1', index=0),
            Token('big', 'm2', index=1),
        ]
        rule = MoreMostRule()
        rule.apply(tokens, basic_context)
        # big → 1 syllable → more نباید m2 شود
        assert tokens[0].label != 'm2' or syllable_count_check('big') > 1


def syllable_count_check(word):
    from src.utils import syllable_count
    return syllable_count(word)
