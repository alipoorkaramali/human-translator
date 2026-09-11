"""قوانین خاص NP"""
from .compound_resplit_rule import CompoundResplitRule
from .m1_of_to_n_rule import M1OfToNRule
from .after_of_label_rule import AfterOfLabelRule
from .much_rule import MuchRule
from .law_sh import LawShRule
from .law_z import LawZRule
from .the_ordinal import TheOrdinalRule
from .final_fix import FinalFixAfterNounRule
from .wordnet_finalize import WordNetFinalizeRule

__all__ = [
    'CompoundResplitRule',
    'M1OfToNRule',
    'AfterOfLabelRule',
    'MuchRule',
    'LawShRule',
    'LawZRule',
    'TheOrdinalRule',
    'FinalFixAfterNounRule',
    'WordNetFinalizeRule',
]
