"""واردکنندهٔ قوانین VP: vp1..vp3 + special"""
import importlib
from ..rule_base import RuleRegistry

_VP1_RULES = [
    ('src.rules.vp.vp1.placeholder_rule', 'Vp1PlaceholderRule'),
]

_VP2_RULES = [
    ('src.rules.vp.vp2.placeholder_rule', 'Vp2PlaceholderRule'),
]

_VP3_RULES = [
    ('src.rules.vp.vp3.placeholder_rule', 'Vp3PlaceholderRule'),
]

_VP_SPECIAL_RULES = [
    ('src.rules.vp.special.infinitive_to_rule', 'InfinitiveToRule'),
    ('src.rules.vp.special.placeholder_rule', 'VpSpecialPlaceholderRule'),
]


def _register(registry: RuleRegistry, specs) -> int:
    count = 0
    for mod_name, cls_name in specs:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            registry.register(cls())
            count += 1
        except (ImportError, AttributeError):
            continue
    return count


def import_vp1_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _VP1_RULES)
    return registry


def import_vp2_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _VP2_RULES)
    return registry


def import_vp3_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _VP3_RULES)
    return registry


def import_vp_special_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _VP_SPECIAL_RULES)
    return registry


def import_vp_rules(registry: RuleRegistry) -> RuleRegistry:
    """ثبت همه قوانین VP (vp1..vp3 + special)."""
    import_vp1_rules(registry)
    import_vp2_rules(registry)
    import_vp3_rules(registry)
    import_vp_special_rules(registry)
    return registry
