"""Placeholder rule — later replace with real logic."""
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule
if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context
class LawZRule(Rule):
    name = "law_z"
    target_label = "special"
    priority = 81
    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        return False
