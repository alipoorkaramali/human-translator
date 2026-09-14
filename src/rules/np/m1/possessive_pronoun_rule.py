"""
قانون m1: ضمایر ملکی مستقل / جانشین NP
  mine, yours, hers, ours, theirs

label   = m1
subtype = possessive pronoun
role    = pronoun/possessive

خودشان یک NP کامل‌اند (This is mine / Yours is better / a friend of mine).
با صفات ملکی (my/your/…) اشتباه نشوند.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_possessive_pronoun

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_DEFAULT = {"mine", "yours", "hers", "ours", "theirs"}


class PossessivePronounRule(Rule):
    name = "possessive_pronoun"
    target_label = "m1"
    priority = 8  # بعد از possessive_adj (7)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        pron = set(getattr(ctx, "possessive_pronoun_set", None) or set()) or set(_DEFAULT)
        changed = False
        for tok in tokens:
            if tok.locked:
                continue
            if " " in tok.word:
                continue
            wl = tok.word.lower()
            if wl not in pron and not is_possessive_pronoun(wl):
                continue
            if tok.label != "m1":
                tok.label = "m1"
                changed = True
            if tok.subtype != "possessive pronoun":
                tok.subtype = "possessive pronoun"
                changed = True
            if tok.role in ("", "unknown", "determiner/possessive", "pronoun"):
                tok.role = "pronoun/possessive"
                changed = True
        return changed
