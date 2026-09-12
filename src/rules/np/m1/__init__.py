"""قوانین فاز m1 (NP)"""
from .fraction_rule import FractionRule
from .compound_number_rule import CompoundNumberRule
from .unit_of_rule import UnitOfRule
from .simple_of_rule import SimpleOfRule
from .compound_phrase import CompoundPhraseRule
from .some_number_rule import SomeNumberRule
from .double_m1_rule import DoubleM1Rule
from .double_quantifier_rule import DoubleQuantifierRule
from .m1_after_noun_rule import M1AfterNounRule

__all__ = [
    'FractionRule',
    'CompoundNumberRule',
    'UnitOfRule',
    'SimpleOfRule',
    'CompoundPhraseRule',
    'SomeNumberRule',
    'DoubleM1Rule',
    'DoubleQuantifierRule',
    'M1AfterNounRule',
]
