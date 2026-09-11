"""
قانون نهایی و قوی: more بعد از m1 → حتماً m2

آخرین مرحلهٔ special (بعد از WordNet و بقیه) تا حتی اگر
WordNet برچسب more را N یا adv کرده باشد، اصلاح شود.

مثال:
  2 more books        → more = m2
  many more students  → more = m2
  some more time      → more = m2
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_np_boundary

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class MoreAfterM1FinalRule(Rule):
    name = "more_after_m1_final"
    target_label = "special"
    priority = 98  # خیلی دیر — بعد از WordNet / final_fix

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False

        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked:
                continue
            if tok.word.lower() != "more":
                continue

            has_m1_before = False
            j = i - 1
            while j >= 0:
                prev = tokens[j]

                if is_np_boundary(prev.word):
                    break
                if prev.label in ("m2", "adv") or prev.word.lower() in {",", "and", "but", "or"}:
                    break

                if prev.label == "m1":
                    has_m1_before = True
                    break

                j -= 1

            if has_m1_before and tok.label != "m2":
                tok.label = "m2"
                changed = True

        return changed
