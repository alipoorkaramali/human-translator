"""
قانون ۲: quantifier ساده + of

مثل: "two of", "many of", "three of"

- اگر قبلش در همین NP کمیت‌نما باشد → ترکیب نمی‌شود (دومی m1 نمی‌گیرد)
- وگرنه → ادغام به "X of" با برچسب m1
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import is_np_boundary, number_type

if TYPE_CHECKING:
    from src.core.context import Context

_EXTRA_QUANTS = {
    "all", "some", "no", "any", "every", "each",
    "more", "most", "less", "few", "several",
    "much", "little", "enough",
}


class SimpleOfRule(Rule):
    name = "simple_of"
    target_label = "m1"
    priority = 12

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        simple = getattr(ctx, "simple_set", set()) or set()
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        i = 0
        while i < len(tokens) - 1:
            tok = tokens[i]
            if tok.locked:
                i += 1
                continue

            wl = tok.word.lower()
            nt = tok.numtype or number_type(tok.word, cardinals, ordinals) or ""

            is_quant = wl in simple or nt == "cardinal"
            if not is_quant or tokens[i + 1].word.lower() != "of":
                i += 1
                continue

            # آیا قبلش کمیت‌نما هست؟
            has_previous_quantifier = False
            for j in range(i - 1, max(i - 12, -1), -1):
                prev = tokens[j]
                prev_w = prev.word.lower()
                if is_np_boundary(prev.word) or prev_w in {",", "and", "but", "or"}:
                    break
                prev_nt = prev.numtype or number_type(prev.word, cardinals, ordinals)
                if (
                    prev_w in simple
                    or prev_w in _EXTRA_QUANTS
                    or prev_nt
                ):
                    has_previous_quantifier = True
                    break

            if has_previous_quantifier:
                # دو کمیت‌نما پشت‌سرهم → دومی m1 نمی‌گیرد؛ of را جدا می‌گذاریم
                if tok.label == "m1":
                    tok.label = ""
                    changed = True
                i += 2
                continue

            # امن → ترکیب "X of"
            combined_word = f"{tok.word} of"
            of_tok = tokens[i + 1]
            if of_tok.locked:
                i += 2
                continue

            combined = Token(
                word=combined_word,
                label="m1",
                numtype=nt,
                role="quantifier_phrase (multi-word)",
                index=tok.index,
                original=combined_word,
            )
            tokens[i:i + 2] = [combined]
            changed = True
            i += 1

        return changed
