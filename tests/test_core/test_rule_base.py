# tests/test_core/test_rule_base.py
import pytest
from src.core.rule_base import Rule, RuleRegistry


class DummyRule(Rule):
    name = "dummy"
    target_label = "m1"
    priority = 50

    def apply(self, tokens, ctx):
        return False


class DummyRule2(DummyRule):
    name = "dummy2"
    priority = 10


class TestRuleRegistry:
    def test_register_and_all(self):
        reg = RuleRegistry()
        reg.register(DummyRule())
        assert len(reg.all()) == 1

    def test_sort_by_priority(self):
        reg = RuleRegistry()
        reg.register(DummyRule())   # priority 50
        reg.register(DummyRule2())  # priority 10
        rules = reg.all()
        assert rules[0].name == "dummy2"
        assert rules[1].name == "dummy"

    def test_by_label(self):
        reg = RuleRegistry()
        reg.register(DummyRule())
        assert len(reg.by_label("m1")) == 1
        assert len(reg.by_label("m2")) == 0

    def test_by_name(self):
        reg = RuleRegistry()
        reg.register(DummyRule())
        found = reg.by_name("dummy")
        assert found.name == "dummy"

    def test_by_name_missing(self):
        reg = RuleRegistry()
        with pytest.raises(KeyError):
            reg.by_name("nonexistent")
