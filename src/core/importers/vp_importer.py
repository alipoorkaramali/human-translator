"""واردکنندهٔ قوانین VP — کشف خودکار از vp1..vp3 و special."""
from ..rule_base import RuleRegistry
from .rule_discovery import register_packages

_VP_PACKAGES = (
    "src.rules.vp.vp1",
    "src.rules.vp.vp2",
    "src.rules.vp.vp3",
    "src.rules.vp.special",
)


def import_vp1_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.vp.vp1",))
    return registry


def import_vp2_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.vp.vp2",))
    return registry


def import_vp3_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.vp.vp3",))
    return registry


def import_vp_special_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, ("src.rules.vp.special",))
    return registry


def import_vp_rules(registry: RuleRegistry) -> RuleRegistry:
    register_packages(registry, _VP_PACKAGES)
    return registry
