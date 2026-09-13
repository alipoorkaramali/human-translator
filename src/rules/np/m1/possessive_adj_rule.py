"""
قانون m1: صفات ملکی (my, your, his, her, its, our, their)

label = m1  (جایگاه determiner در NP)
subtype = possessive adj  (سیگنال ترجمه و مسدودسازی ادغام)
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_DEFAULT = {"my", "your", "his", "her", "its", "our", "their"}


class PossessiveAdjRule(Rule):
    name = "possessive_adj"
    target_label = "m1"
    priority = 5  # زود، قبل از quantifierهای دیگر

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        poss = set(getattr(ctx, "possessive_set", None) or set()) or set(_DEFAULT)
        changed = False
        for tok in tokens:
            if tok.locked:
                continue
            if " " in tok.word:
                continue
            if tok.word.lower() not in poss:
                continue
            if tok.label != "m1":
                tok.label = "m1"
                changed = True
            if tok.subtype != "possessive adj":
                tok.subtype = "possessive adj"
                changed = True
            if tok.role in ("", "unknown"):
                tok.role = "determiner/possessive"
                changed = True
        return changed
