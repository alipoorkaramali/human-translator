"""واردکنندهٔ ۲: قوانین m1 — هر Rule که موجود باشد ثبت میشود."""
from ..rule_base import RuleRegistry


# هر tuple: (ماژول، نام کلاس)
_M1_RULES = [
    ('src.rules.m1.fraction_rule',       'FractionRule'),
    ('src.rules.m1.article_rule',        'ArticleRule'),
    ('src.rules.m1.demonstrative_rule',  'DemonstrativeRule'),
    ('src.rules.m1.simple_of_rule',      'SimpleOfRule'),
    ('src.rules.m1.compound_phrase',     'CompoundPhraseRule'),
    ('src.rules.m1.unit_of_rule',        'UnitOfRule'),
    ('src.rules.m1.some_number_rule',    'SomeNumberRule'),
    ('src.rules.m1.double_m1_rule',      'DoubleM1Rule'),
    ('src.rules.m1.m1_after_noun_rule',  'M1AfterNounRule'),
]


def import_m1_rules(registry: RuleRegistry) -> RuleRegistry:
    import importlib
    for mod_name, cls_name in _M1_RULES:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            registry.register(cls())
        except (ImportError, AttributeError):
            continue
    return registry
