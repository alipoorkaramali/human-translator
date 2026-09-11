"""قانون: اگر بعد از اسم یک عدد بیاید، عدد را m1 می‌زند."""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class M1AfterNounRule(Rule):
    name = "m1_after_noun"
    target_label = "m1"
    priority = 70

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        for i in range(1, len(tokens)):
            tok = tokens[i]
            if tok.locked:
                continue
            prev = tokens[i - 1]
            is_num = tok.numtype in ("cardinal", "ordinal") or tok.word.isdigit()
            if not is_num:
                continue
            if prev.label in ("", "N") and prev.word.isalpha():
                if tok.label != "m1":
                    tok.label = "m1"
                    changed = True
        return changed
