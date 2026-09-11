"""قانون: some + عدد → برچسب m1"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class SomeNumberRule(Rule):
    name = "some_number"
    target_label = "m1"
    priority = 40

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        for i, tok in enumerate(tokens):
            if tok.locked:
                continue
            if tok.word.lower() != "some":
                continue
            # some + عدد بعدی
            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                if nxt.numtype in ("cardinal", "ordinal") or nxt.word.isdigit():
                    if tok.label != "m1":
                        tok.label = "m1"
                        changed = True
                    if not nxt.locked and nxt.label != "m1":
                        nxt.label = "m1"
                        changed = True
        return changed
