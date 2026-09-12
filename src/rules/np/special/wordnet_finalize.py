"""
نقش‌های معنایی و تنظیمات نهایی — بدون POS از WordNet.

POS ساختاری (N/V/m2/adv) توسط SpacyPosRule انجام می‌شود.
این Rule:
  - role برای m1 چندکلمه‌ای / quantifier
  - intensifier → adv
  - more/most قبل از صفت چندسیلابی → adv (اگر m1 قبل نباشد)
  - of / punctuation / articles
  - fallback نقش از روی برچسب
"""
from typing import List, TYPE_CHECKING
import re

from src.core.rule_base import Rule
from src.utils import syllable_count, is_np_boundary

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_LABEL_ROLE = {
    "m1": "determiner/quantifier",
    "m2": "adjective",
    "adv": "adverb",
    "N": "noun",
    "V": "verb",
    "": "function word",
}


class WordNetFinalizeRule(Rule):
    name = "wordnet_finalize"
    target_label = "special"
    priority = 88

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        intensifiers = getattr(ctx, "intensifier_set", set()) or set()

        for tok in tokens:
            if tok.locked:
                continue
            w = tok.word
            label = tok.label
            is_multi = " " in w

            if is_multi and label == "m1":
                if tok.role != "quantifier_phrase (multi-word)":
                    tok.role = "quantifier_phrase (multi-word)"
                    changed = True
                continue

            if label == "m1" and tok.role in ("", "unknown"):
                tok.role = "determiner/quantifier"
                changed = True

            # ordinal را TheOrdinalRule مدیریت می‌کند
            if tok.numtype == "ordinal":
                continue

        # intensifierها
        for tok in tokens:
            if tok.locked:
                continue
            if tok.word.lower() in intensifiers:
                if tok.label != "adv" or tok.role != "adverb (intensifier)":
                    tok.label = "adv"
                    tok.role = "adverb (intensifier)"
                    changed = True

        # more/most → adv فقط اگر m1 قبلش در NP نباشد
        for i in range(len(tokens) - 1):
            tok = tokens[i]
            if tok.locked or tok.word.lower() not in ("more", "most"):
                continue
            nxt = tokens[i + 1]
            if nxt.label != "m2" or syllable_count(nxt.word) <= 1:
                continue

            has_m1 = False
            j = i - 1
            while j >= 0:
                prev = tokens[j]
                if is_np_boundary(prev.word):
                    break
                if prev.label in ("m2", "adv") or prev.word.lower() in {
                    ",", "and", "but", "or"
                }:
                    break
                if prev.label == "m1":
                    has_m1 = True
                    break
                j -= 1

            if has_m1:
                continue

            if tok.label != "adv" or tok.role != "adverb (comparative/superlative)":
                tok.label = "adv"
                tok.role = "adverb (comparative/superlative)"
                changed = True

        for tok in tokens:
            if tok.locked:
                continue
            lw = tok.word.lower()
            if lw == "of":
                if tok.label != "" or tok.role != "preposition":
                    tok.label = ""
                    tok.role = "preposition"
                    changed = True
            elif re.match(r"^[^\w\s]$", tok.word):
                if tok.role != "punctuation":
                    tok.role = "punctuation"
                    changed = True
            elif lw in {"a", "an", "the"}:
                if tok.role != "determiner/article":
                    tok.role = "determiner/article"
                    changed = True

            if tok.role in ("", "unknown"):
                tok.role = _LABEL_ROLE.get(tok.label, "unknown")
                changed = True

        return changed
