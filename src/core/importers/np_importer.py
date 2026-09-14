"""واردکنندهٔ قوانین NP — کشف خودکار از پوشه‌های m1..m5 و special.

قانون جدید:
  1) فایل را زیر src/rules/np/<phase>/ بگذار (مثلاً m1 یا special)
  2) کلاس از Rule ارث ببرد (name, target_label, priority, apply)
  3) ذخیره کن — بدون ویرایش این فایل و بدون rebuild داکر (با mount بودن src/)
"""
from ..rule_base import RuleRegistry
from .rule_discovery import register_packages

_NP_PACKAGES = (
    "src.rules.np.m1",
    "src.rules.np.m2",
    "src.rules.np.m3",
    "src.rules.np.m4",
    "src.rules.np.m5",
    "src.rules.np.special",
)


def import_m1_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.np.m1",))
    return registry


def import_m2_to_m5(registry: RuleRegistry) -> RuleRegistry:
    register_packages(
        registry,
        ("src.rules.np.m2", "src.rules.np.m3", "src.rules.np.m4", "src.rules.np.m5"),
    )
    return registry


def import_np_special_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.np.special",))
    return registry


def import_np_span_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.np.special",))
    return registry


def import_np_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, _NP_PACKAGES)
    return registry
