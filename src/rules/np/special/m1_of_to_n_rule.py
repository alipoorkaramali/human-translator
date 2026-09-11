"""
قانون ۲: m1 + of → آن m1 به N تبدیل می‌شود.
مثال: plenty of → plenty=N
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class M1OfToNRule(Rule):
    name = "m1_of_to_n"
    target_label = "special"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        for i in range(len(tokens) - 1):
            tok = tokens[i]
            if tok.locked:
                continue
            if tok.label == "m1" and tokens[i + 1].word.lower() == "of":
                tok.label = "N"
                changed = True
        return changed
