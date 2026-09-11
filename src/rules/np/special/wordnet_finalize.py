"""Placeholder rule — later replace with real logic."""
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule
if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context
class WordNetFinalizeRule(Rule):
    name = "wordnet_finalize"
    target_label = "special"
    priority = 88
    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        return False
