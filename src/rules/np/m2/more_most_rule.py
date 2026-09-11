"""
قانون ۴ + ۷:
- more/most بعد از det/poss → adv
- more وقتی قبلش m1 در همین NP باشد → حتماً m2
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_possessive_or_s, is_np_boundary

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class MoreMostRule(Rule):
    name = "more_most"
    target_label = "m2"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        articles = getattr(ctx, "article_set", set()) or set()
        demos = getattr(ctx, "demotrative_set", set()) or set()

        # قانون ۷ اولویت‌دار: more بعد از m1 → m2
        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked or tok.word.lower() != "more":
                continue
            has_m1 = False
            j = i - 1
            while j >= 0:
                prev = tokens[j]
                if is_np_boundary(prev.word):
                    break
                if prev.label in ("m2", "adv") or prev.word.lower() in {",", "and", "but", "or"}:
                    break
                if prev.label == "m1":
                    has_m1 = True
                    break
                j -= 1
            if has_m1 and tok.label != "m2":
                tok.label = "m2"
                changed = True

        # قانون ۴: more/most بعد از det/poss → adv
        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked:
                continue
            if tok.word.lower() not in ("more", "most"):
                continue
            if tok.label not in ("m1", "m2"):
                continue
            # اگر همین دور m2 از قانون ۷ گرفته، دست نزن
            if tok.label == "m2":
                # چک کن آیا از قانون ۷ آمده (m1 قبلش)
                j = i - 1
                skip = False
                while j >= 0:
                    if is_np_boundary(tokens[j].word):
                        break
                    if tokens[j].label == "m1":
                        skip = True
                        break
                    if tokens[j].label in ("m2", "adv"):
                        break
                    j -= 1
                if skip:
                    continue
            prev = tokens[i - 1].word.lower()
            if prev in articles | demos or is_possessive_or_s(prev):
                tok.label = "adv"
                changed = True

        return changed
