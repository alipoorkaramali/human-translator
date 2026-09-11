"""Placeholder rule — later replace with real logic."""
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule
if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context
class HyphenatedRule(Rule):
    name = "hyphenated"
    target_label = "m2"
    priority = 60
    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        return False
