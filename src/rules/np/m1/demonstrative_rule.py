"""demonstrative this/that/these/those → m1"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class DemonstrativeRule(Rule):
    name = "demonstrative"
    target_label = "m1"
    priority = 21

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        demos = getattr(ctx, "demotrative_set", set()) or {
            "this", "that", "these", "those"
        }

        for tok in tokens:
            if tok.locked:
                continue
            if tok.word.lower() in demos:
                if tok.label != "m1":
                    tok.label = "m1"
                    tok.role = "determiner/demonstrative"
                    changed = True
        return changed
