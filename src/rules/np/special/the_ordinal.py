"""
قانون نهایی ordinal (هم‌تراز نوت‌بوک):

  • فقط وقتی دقیقاً قبلش "the" باشد → ترکیب "the ORDINAL" و برچسب m1
  • در همهٔ حالت‌های دیگر → ordinal تک‌کلمه = adv
  • توکن ادغام‌شدهٔ «the ORDINAL» هرگز دوباره adv نمی‌شود
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import number_type

if TYPE_CHECKING:
    from src.core.context import Context


def _is_single_ordinal(tok, cardinals, ordinals) -> bool:
    """فقط ordinal تک‌کلمه — نه «the first» ادغام‌شده."""
    if " " in tok.word:
        return False
    if tok.subtype == "ordinal":
        return True
    return number_type(tok.word, cardinals, ordinals) == "ordinal"


def _force_the_ordinal_m1(tokens, cardinals, ordinals) -> bool:
    """هر توکن «the + ordinal» باید m1 بماند."""
    changed = False
    for tok in tokens:
        w = tok.word.lower()
        if not w.startswith("the "):
            continue
        last = w.split()[-1]
        if tok.subtype == "ordinal" or number_type(last, cardinals, ordinals) == "ordinal":
            if tok.label != "m1":
                tok.label = "m1"
                changed = True
            if tok.role in ("", "unknown", "adverb", "adverb (intensifier)"):
                tok.role = "determiner/quantifier"
                changed = True
            if not tok.locked:
                tok.locked = True
                changed = True
    return changed


class TheOrdinalRule(Rule):
    name = "the_ordinal"
    target_label = "special"
    priority = 82

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        # دفاعی قبل از حلقه
        if _force_the_ordinal_m1(tokens, cardinals, ordinals):
            changed = True

        i = 0
        while i < len(tokens):
            if i >= len(tokens) - 1:
                break

            nxt = tokens[i + 1]
            if not _is_single_ordinal(nxt, cardinals, ordinals):
                i += 1
                continue

            cur = tokens[i]
            # the + ordinal تک‌کلمه → ادغام m1
            if cur.word.lower() == "the" and cur.label in ("", "m1"):
                combined = Token(
                    word=f"the {nxt.word}",
                    label="m1",
                    subtype="ordinal",
                    role="determiner/quantifier",
                    index=cur.index,
                    original=f"{cur.original} {nxt.original}".strip(),
                    locked=True,  # قفل تا دور بعد خراب نشود
                )
                tokens[i:i + 2] = [combined]
                changed = True
                # i ثابت؛ توکن بعدی بعد از ادغام بررسی می‌شود
            else:
                # ordinal تنها (بدون the) → adv
                if not nxt.locked and nxt.label != "adv":
                    nxt.label = "adv"
                    nxt.role = "adverb"
                    changed = True
                i += 1

        # دفاعی بعد از حلقه
        if _force_the_ordinal_m1(tokens, cardinals, ordinals):
            changed = True

        return changed
