"""
قانون: tens of / hundreds of / thousands of / millions of / ...

اگر پشت‌سرهم بیایند → یک توکن m1 مرکب.

مثال:
  hundreds of                    → "hundreds of" = m1
  tens of thousands of           → "tens of thousands of" = m1
  millions of billions of        → ادغام زنجیره‌ای
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context

_UNIT_BASES = {
    "ten", "tens", "hundred", "hundreds", "thousand", "thousands",
    "million", "millions", "billion", "billions", "trillion", "trillions",
}


class UnitOfRule(Rule):
    name = "unit_of"
    target_label = "m1"
    priority = 8  # بعد از fraction، قبل از some_number

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        i = 0
        while i < len(tokens) - 1:
            tok = tokens[i]
            if tok.locked:
                i += 1
                continue

            wl = tok.word.lower()
            if wl not in _UNIT_BASES or tokens[i + 1].word.lower() != "of":
                i += 1
                continue

            # شروع زنجیره: unit + of
            end = i + 2
            parts = [tok.word, tokens[i + 1].word]

            # ادامهٔ زنجیره: unit of unit of ...
            while end < len(tokens) - 1:
                nxt_w = tokens[end].word.lower()
                if nxt_w in _UNIT_BASES and tokens[end + 1].word.lower() == "of":
                    parts.append(tokens[end].word)
                    parts.append(tokens[end + 1].word)
                    end += 2
                else:
                    break

            combined_word = " ".join(parts)
            # اگر از قبل همین توکن مرکب باشد
            if end == i + 1:
                i += 1
                continue

            if end == i + 2 and tok.word == combined_word:
                if tok.label != "m1":
                    tok.label = "m1"
                    tok.role = "quantifier_phrase (multi-word)"
                    changed = True
                i = end
                continue

            combined = Token(
                word=combined_word,
                label="m1",
                numtype="",
                role="quantifier_phrase (multi-word)",
                index=tok.index,
                original=combined_word,
            )
            tokens[i:end] = [combined]
            changed = True
            i += 1

        return changed
