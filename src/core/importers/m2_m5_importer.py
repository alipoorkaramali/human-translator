"""واردکنندهٔ ۳: قوانین m2 تا m5"""
import importlib
from ..rule_base import RuleRegistry


_M2_RULES = [
    ('src.rules.m2.more_most_rule',       'MoreMostRule'),
    ('src.rules.m2.little_rule',          'LittleRule'),
    ('src.rules.m2.hyphenated_rule',      'HyphenatedRule'),
]
_M3_RULES = [
    ('src.rules.m3.possessive_rule',      'PossessiveRule'),
]
_M4_RULES = [
    ('src.rules.m4.number_after_noun_rule', 'NumberAfterNounRule'),
    ('src.rules.m4.ordinal_rule',           'OrdinalRule'),
]
_M5_RULES = [
    ('src.rules.m5.fallback_rule',        'FallbackRule'),
]


def _register(registry, specs):
    for mod_name, cls_name in specs:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            registry.register(cls())
        except (ImportError, AttributeError):
            continue


def import_m2_rules(registry):
    _register(registry, _M2_RULES)


def import_m3_rules(registry):
    _register(registry, _M3_RULES)


def import_m4_rules(registry):
    _register(registry, _M4_RULES)


def import_m5_rules(registry):
    _register(registry, _M5_RULES)


def import_m2_to_m5(registry: RuleRegistry) -> RuleRegistry:
    import_m2_rules(registry)
    import_m3_rules(registry)
    import_m4_rules(registry)
    import_m5_rules(registry)
    return registry
