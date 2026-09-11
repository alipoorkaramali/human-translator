# tests/test_importers/test_m1_importer.py
import pytest

importer = pytest.importorskip("src.core.importers.m1_importer")
RuleRegistry = pytest.importorskip("src.core.rule_base").RuleRegistry


class TestM1Importer:
    def test_imports_all_rules(self):
        reg = RuleRegistry()
        importer.import_m1_rules(reg)
        rules = reg.by_label("m1")
        assert len(rules) >= 3

    def test_rule_names(self):
        reg = RuleRegistry()
        importer.import_m1_rules(reg)
        names = {r.name for r in reg.by_label("m1")}
        # حداقل باید SomeNumberRule باشد
        assert any('some' in n.lower() for n in names)

    def test_all_rules_have_priority(self):
        reg = RuleRegistry()
        importer.import_m1_rules(reg)
        for r in reg.by_label("m1"):
            assert isinstance(r.priority, int)
