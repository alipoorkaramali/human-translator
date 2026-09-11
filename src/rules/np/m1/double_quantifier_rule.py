"""
قانون ۵: دو quantifier پشت‌سرهم (به جز some).
quantifier دوم → اگر compound باشد '' وگرنه adv.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class DoubleQuantifierRule(Rule):
    name = "double_quantifier"
    target_label = "m1"
    priority = 50

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        simple = getattr(ctx, "simple_set", set()) or set()
        compound = getattr(ctx, "compound_set", set()) or set()

        for i in range(1, len(tokens)):
            cur = tokens[i]
            if cur.locked:
                continue
            prev = tokens[i - 1]
            prev_w = prev.word.lower()
            cur_w = cur.word.lower()

            prev_q = (
                prev_w in simple
                or prev_w in compound
                or prev.numtype in ("cardinal", "ordinal")
            )
            cur_q = (
                cur_w in simple
                or cur_w in compound
                or cur.numtype in ("cardinal", "ordinal")
            )
            if prev_q and cur_q and prev_w != "some":
                new_label = "" if cur_w in compound else "adv"
                if cur.label != new_label:
                    cur.label = new_label
                    changed = True
        return changed
