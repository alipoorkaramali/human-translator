"""
قانون فقط برای enough:
  اگر بلافاصله بعد از صفت (m2) بیاید → adv
  در بقیهٔ حالات (enough water, enough books) دست نمی‌زند (m1 می‌ماند).

مثال:
  good enough       → enough = adv
  big enough        → enough = adv
  beautiful enough  → enough = adv
  enough water      → بدون تغییر
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class EnoughAfterAdjRule(Rule):
    name = "enough_after_adj"
    target_label = "special"
    priority = 45

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False

        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked:
                continue
            if tok.word.lower() != "enough":
                continue

            prev = tokens[i - 1]
            # فقط وقتی دقیقاً بعد از صفت (m2) باشد
            if prev.label == "m2":
                if tok.label != "adv":
                    tok.label = "adv"
                    tok.role = "adverb"
                    changed = True

        return changed
