"""قوانین خاص NP"""
from .law_sh import LawShRule
from .law_z import LawZRule
from .the_ordinal import TheOrdinalRule
from .final_fix import FinalFixAfterNounRule
from .wordnet_finalize import WordNetFinalizeRule
from .much_rule import MuchRule

__all__ = ["LawShRule", "LawZRule", "TheOrdinalRule", "FinalFixAfterNounRule", "WordNetFinalizeRule", "MuchRule"]
