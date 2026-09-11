"""
آخرین اصلاح quantifier/عدد بعد از اسم — حتماً بعد از WordNet.

اگر m1 بعد از N در همین NP باشد و بینشان of نباشد:
  • عدد → m4
  • quantifier غیرعددی → adv
article/demonstrative همیشه m1 می‌مانند.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_np_boundary, number_type

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_ALWAYS_M1 = {"a", "an", "the", "this", "that", "these", "those"}


class FinalFixAfterNounRule(Rule):
    name = "final_fix_after_noun"
    target_label = "special"
    priority = 92  # بعد از wordnet_finalize (88)، قبل از more_after_m1_final (98)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked or tok.label != "m1":
                continue

            low = tok.word.lower()
            if low in _ALWAYS_M1:
                continue

            is_number = tok.numtype in ("cardinal", "ordinal") or (
                number_type(tok.word, cardinals, ordinals) is not None
            )

            has_noun_without_of = False
            for j in range(i - 1, -1, -1):
                prev = tokens[j]
                if is_np_boundary(prev.word):
                    break
                if prev.word.lower() == "of":
                    break
                if prev.label == "N":
                    has_noun_without_of = True
                    break

            if has_noun_without_of:
                new_label = "m4" if is_number else "adv"
                if tok.label != new_label:
                    tok.label = new_label
                    changed = True

        return changed
