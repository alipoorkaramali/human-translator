"""واردکنندهٔ قوانین NP: m1..m5 + special"""
import importlib
from ..rule_base import RuleRegistry

_M1_RULES = [
    ('src.rules.np.m1.fraction_rule', 'FractionRule'),
    ('src.rules.np.m1.article_rule', 'ArticleRule'),
    ('src.rules.np.m1.demonstrative_rule', 'DemonstrativeRule'),
    ('src.rules.np.m1.simple_of_rule', 'SimpleOfRule'),
    ('src.rules.np.m1.compound_phrase', 'CompoundPhraseRule'),
    ('src.rules.np.m1.unit_of_rule', 'UnitOfRule'),
    ('src.rules.np.m1.some_number_rule', 'SomeNumberRule'),
    ('src.rules.np.m1.double_m1_rule', 'DoubleM1Rule'),
    ('src.rules.np.m1.double_quantifier_rule', 'DoubleQuantifierRule'),
    ('src.rules.np.m1.m1_after_noun_rule', 'M1AfterNounRule'),
]

_M2_RULES = [
    ('src.rules.np.m2.more_most_rule', 'MoreMostRule'),
    ('src.rules.np.m2.little_rule', 'LittleRule'),
    ('src.rules.np.m2.hyphenated_rule', 'HyphenatedRule'),
]

_M3_RULES = [
    ('src.rules.np.m3.possessive_rule', 'PossessiveRule'),
]

_M4_RULES = [
    ('src.rules.np.m4.number_after_noun_rule', 'NumberAfterNounRule'),
    ('src.rules.np.m4.ordinal_rule', 'OrdinalRule'),
]

_M5_RULES = [
    ('src.rules.np.m5.fallback_rule', 'FallbackRule'),
]

_NP_SPECIAL_RULES = [
    ('src.rules.np.special.compound_resplit_rule', 'CompoundResplitRule'),
    ('src.rules.np.special.m1_of_to_n_rule', 'M1OfToNRule'),
    ('src.rules.np.special.after_of_label_rule', 'AfterOfLabelRule'),
    ('src.rules.np.special.much_rule', 'MuchRule'),
    ('src.rules.np.special.law_sh', 'LawShRule'),
    ('src.rules.np.special.law_z', 'LawZRule'),
    ('src.rules.np.special.the_ordinal', 'TheOrdinalRule'),
    ('src.rules.np.special.final_fix', 'FinalFixAfterNounRule'),
    ('src.rules.np.special.wordnet_finalize', 'WordNetFinalizeRule'),
    # آخرین اصلاح: بعد از WordNet
    ('src.rules.np.special.more_after_m1_final_rule', 'MoreAfterM1FinalRule'),
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


def import_m1_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _M1_RULES)
    return registry


def import_m2_to_m5(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _M2_RULES)
    _register(registry, _M3_RULES)
    _register(registry, _M4_RULES)
    _register(registry, _M5_RULES)
    return registry


def import_np_special_rules(registry: RuleRegistry) -> RuleRegistry:
    _register(registry, _NP_SPECIAL_RULES)
    return registry


def import_np_rules(registry: RuleRegistry) -> RuleRegistry:
    """ثبت همه قوانین NP (m1..m5 + special)."""
    import_m1_rules(registry)
    import_m2_to_m5(registry)
    import_np_special_rules(registry)
    return registry
