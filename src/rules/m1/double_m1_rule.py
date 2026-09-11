"""قانون: دو توکن متوالی m1 را قفل/یکدست می‌کند."""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class DoubleM1Rule(Rule):
    name = "double_m1"
    target_label = "m1"
    priority = 60

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        for i in range(len(tokens) - 1):
            a, b = tokens[i], tokens[i + 1]
            if a.locked or b.locked:
                continue
            if a.label == "m1" and b.label == "m1":
                # هر دو را locked نگه می‌داریم تا قوانین بعدی دست نزنند
                if not a.locked:
                    a.locked = True
                    changed = True
                if not b.locked:
                    b.locked = True
                    changed = True
        return changed
