"""
قانون نهایی ordinal (هم‌تراز نوت‌بوک):

  • فقط وقتی دقیقاً قبلش "the" باشد → ترکیب "the ORDINAL" و برچسب m1
  • در همهٔ حالت‌های دیگر → ordinal = adv
  • اگر از قبل m4 یا adv باشد → دست نزن
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import number_type

if TYPE_CHECKING:
    from src.core.context import Context


class TheOrdinalRule(Rule):
    name = "the_ordinal"
    target_label = "special"
    priority = 82

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        # دفاعی: اگر قبلاً «the ORDINAL» ادغام شده ولی label خراب شده
        for tok in tokens:
            if tok.locked:
                continue
            w = tok.word.lower()
            if w.startswith("the ") and (
                tok.subtype == "ordinal"
                or number_type(tok.word.split()[-1], cardinals, ordinals) == "ordinal"
            ):
                if tok.label != "m1":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True

        i = 0
        while i < len(tokens):
            if i >= len(tokens) - 1:
                break

            nxt = tokens[i + 1]
            is_ord = nxt.subtype == "ordinal" or (
                number_type(nxt.word, cardinals, ordinals) == "ordinal"
            )
            if not is_ord:
                i += 1
                continue

            cur = tokens[i]
            # the + ordinal → همیشه ادغام (حتی اگر first قبلاً adv/m4 شده باشد)
            if cur.word.lower() == "the" and cur.label in ("", "m1"):
                combined = Token(
                    word=f"the {nxt.word}",
                    label="m1",
                    subtype="ordinal",
                    role="determiner/quantifier",
                    index=cur.index,
                    original=f"{cur.original} {nxt.original}".strip(),
                    locked=False,
                )
                tokens[i:i + 2] = [combined]
                changed = True
            else:
                # همهٔ حالت‌های دیگر → ordinal = adv
                if not nxt.locked and nxt.label != "adv":
                    nxt.label = "adv"
                    nxt.role = "adverb"
                    changed = True
                i += 1

        return changed
