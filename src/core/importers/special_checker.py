"""واردکنندهٔ ۴: حالتهای خاص"""
import importlib
from ..rule_base import RuleRegistry


_SPECIAL_RULES = [
    ('src.rules.special.law_sh',            'LawShRule'),
    ('src.rules.special.law_z',             'LawZRule'),
    ('src.rules.special.the_ordinal',       'TheOrdinalRule'),
    ('src.rules.special.final_fix',         'FinalFixAfterNounRule'),
    ('src.rules.special.wordnet_finalize',  'WordNetFinalizeRule'),
    ('src.rules.special.much_rule',         'MuchRule'),
]


def import_special_rules(registry: RuleRegistry) -> RuleRegistry:
    for mod_name, cls_name in _SPECIAL_RULES:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            registry.register(cls())
        except (ImportError, AttributeError):
            continue
    return registry
