"""
قانون ۳: عبارات چندکلمه‌ای (تا ۵ کلمه) از phrases_set / compound_set

با بلاک:
  - ملکی در همین NP قبل از عبارت
  - m2 / adv قبل از عبارت در همین NP
  - ملکی داخل خود عبارت
  - quantifier قبلی در همین NP
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import is_np_boundary, is_possessive_or_s, number_type

if TYPE_CHECKING:
    from src.core.context import Context

_EXTRA_QUANTS = {
    "all", "some", "no", "any", "every", "each",
    "more", "most", "less", "few", "several",
    "much", "little", "enough",
}


class CompoundPhraseRule(Rule):
    name = "compound_phrase"
    target_label = "m1"
    priority = 15

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        phrases = getattr(ctx, "phrases_set", set()) or set()
        compounds = getattr(ctx, "compound_set", set()) or set()
        phrase_bank = phrases | compounds
        simple = getattr(ctx, "simple_set", set()) or set()
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

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

                # بلاک: ملکی یا m2/adv قبل از عبارت در همین NP
                blocked_by_possessive = False
                blocked_by_modifier = False
                for j in range(i - 1, -1, -1):
                    if is_np_boundary(tokens[j].word):
                        break
                    if is_possessive_or_s(tokens[j].word):
                        blocked_by_possessive = True
                    if tokens[j].label in ("m2", "adv"):
                        blocked_by_modifier = True

                if blocked_by_possessive or blocked_by_modifier:
                    continue

                # ملکی داخل خود عبارت
                if any(is_possessive_or_s(t.word) for t in phrase_tokens):
                    continue

                # quantifier قبلی
                has_previous_quantifier = False
                for j in range(i - 1, max(i - 12, -1), -1):
                    prev = tokens[j]
                    prev_w = prev.word.lower()
                    if is_np_boundary(prev.word) or prev_w in {",", "and", "but", "or"}:
                        break
                    prev_nt = prev.numtype or number_type(prev.word, cardinals, ordinals)
                    if prev_w in simple or prev_w in _EXTRA_QUANTS or prev_nt:
                        has_previous_quantifier = True
                        break

                if has_previous_quantifier:
                    continue

                if phrase not in phrase_bank:
                    continue

                # ادغام
                if length == 1:
                    if phrase_tokens[0].label != "m1":
                        phrase_tokens[0].label = "m1"
                        phrase_tokens[0].role = "quantifier_phrase (multi-word)"
                        changed = True
                    i += 1
                    found = True
                    break

                combined = Token(
                    word=" ".join(t.word for t in phrase_tokens),
                    label="m1",
                    numtype="",
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
