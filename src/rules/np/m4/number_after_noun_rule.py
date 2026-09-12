"""
منطق m1-بعد-از-اسم فقط در FinalFixAfterNounRule (بعد از WordNet) اجرا می‌شود.
این Rule عمداً غیرفعال است تا دوباره‌کاری/تناقض نباشد.
"""
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule
if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

class NumberAfterNounRule(Rule):
    name = "number_after_noun_disabled"
    target_label = "m4"
    priority = 40
    enabled = False

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        return False
