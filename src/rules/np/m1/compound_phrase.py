"""
قانون ۳: عبارات چندکلمه‌ای quantifier از phrases_set / compound_set

فقط انگلیسی معیار:
  • بلندترین عبارت موجود در بانک را ادغام می‌کند
  • بدون بلاک‌های محافظه‌کارانه (ملکی/m2/adv/quantifier قبلی)
  • اگر «lot of» مچ شد و قبلش a/an بود و «a lot of» در بانک است → گسترش به چپ
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context


class CompoundPhraseRule(Rule):
    name = "compound_phrase"
    target_label = "m1"
    priority = 15

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        phrases = getattr(ctx, "phrases_set", set()) or set()
        compounds = getattr(ctx, "compound_set", set()) or set()
        phrase_bank = phrases | compounds

        i = 0
        while i < len(tokens):
            if tokens[i].locked:
                i += 1
                continue

            found = False
            max_len = min(6, len(tokens) - i + 1)
            for length in range(max_len, 1, -1):
                if i + length > len(tokens):
                    continue
                phrase_tokens = tokens[i:i + length]
                phrase = " ".join(t.word for t in phrase_tokens).lower()

                if phrase not in phrase_bank:
                    continue

                # اگر «lot of» مچ شد ولی قبلش a/an است و «a lot of» در بانک است → گسترش به چپ
                if i > 0 and not tokens[i - 1].locked:
                    prev_w = tokens[i - 1].word.lower()
                    if prev_w in {"a", "an"}:
                        extended = f"{prev_w} {phrase}"
                        if extended in phrase_bank:
                            phrase_tokens = tokens[i - 1:i + length]
                            length = length + 1
                            i = i - 1

                combined = Token(
                    word=" ".join(t.word for t in phrase_tokens),
                    label="m1",
                    subtype="",
                    role="quantifier_phrase (multi-word)",
                    index=phrase_tokens[0].index,
                    original=" ".join(t.word for t in phrase_tokens),
                )
                tokens[i:i + length] = [combined]
                changed = True
                i += 1
                found = True
                break

            if not found:
                i += 1

        return changed
