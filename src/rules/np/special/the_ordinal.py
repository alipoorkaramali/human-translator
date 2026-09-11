"""
قانون the + ordinal:

  • فقط "the" + ordinal (بدون مداخله بینشان) → ordinal = m1
  • ordinal تنها یا بعد از اسم / بدون the بلافاصله قبل → m4
  • بقیهٔ حالت‌ها دست‌نخورده

مثال:
  the first book   → first = m1
  first book       → first = m4
  chapter first    → first = m4
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import number_type

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class TheOrdinalRule(Rule):
    name = "the_ordinal"
    target_label = "special"
    priority = 82

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue

            is_ord = tok.numtype == "ordinal" or (
                number_type(tok.word, cardinals, ordinals) == "ordinal"
            )
            if not is_ord:
                continue

            # فقط the بلافاصله قبل (بدون فاصله/مداخله — توکن قبلی)
            the_immediately_before = (
                i > 0 and tokens[i - 1].word.lower() == "the"
            )

            if the_immediately_before:
                # the + ordinal → m1
                if tok.label != "m1":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True
                # the را هم m1 نگه دار
                prev = tokens[i - 1]
                if not prev.locked and prev.label != "m1":
                    prev.label = "m1"
                    prev.role = "determiner/article"
                    changed = True
            else:
                # ordinal بدون the چسبیده → m4 (مگر از قبل برچسب قفل‌شده)
                if tok.label not in ("m4", "adv"):
                    # adv ممکن است از WordNet ordinal آمده باشد؛ دست نزن اگر adv است
                    if tok.label != "m4":
                        tok.label = "m4"
                        tok.role = "ordinal number"
                        changed = True

        return changed
