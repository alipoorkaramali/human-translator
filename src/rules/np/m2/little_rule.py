"""
قانون little / a little بر اساس countable / uncountable:

  • little + uncountable noun → m1 (quantifier)
  • little + countable noun   → m2 (adjective = small)
  • a little                  → همیشه m1 (حتی با countable)

مثال:
  little water     → m1
  little book      → m2
  a little water   → m1
  a little book    → m1
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_uncountable_noun, is_np_boundary

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class LittleRule(Rule):
    name = "little"
    target_label = "m2"
    priority = 30

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue
            if tok.word.lower() != "little":
                continue

            # --- a little → همیشه m1 ---
            if i >= 1 and tokens[i - 1].word.lower() == "a":
                if tok.label != "m1":
                    tok.label = "m1"
                    changed = True
                # خودِ a را هم m1 نگه می‌داریم اگر خالی/متفاوت بود
                prev = tokens[i - 1]
                if not prev.locked and prev.label not in ("m1",):
                    prev.label = "m1"
                    changed = True
                continue

            # --- little + noun بعدی ---
            noun = self._next_noun(tokens, i)
            if noun is None:
                continue

            if is_uncountable_noun(noun.word, ctx):
                new_label = "m1"  # quantifier
            else:
                new_label = "m2"  # adjective = small

            if tok.label != new_label:
                tok.label = new_label
                changed = True

        return changed

    @staticmethod
    def _next_noun(tokens: List["Token"], i: int):
        """اولین کاندید اسم بعد از little در همین NP."""
        j = i + 1
        while j < len(tokens):
            t = tokens[j]
            w = t.word.lower()
            if is_np_boundary(w):
                return None
            # از روی صفت/قید/عدد رد شو تا به اسم برسیم
            if t.label in ("m2", "adv", "m1") or t.numtype:
                j += 1
                continue
            if t.label == "N":
                return t
            # بدون برچسب: احتمالاً اسم
            if t.label == "" and w.isalpha():
                return t
            j += 1
        return None
