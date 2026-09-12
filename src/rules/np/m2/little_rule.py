"""
منتقل شد به special/little_rule.py (بعد از WordNet).
این فایل فقط برای سازگاری import باقی مانده و کاری نمی‌کند.
"""
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule
if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

class LittleRule(Rule):
    name = "little_m2_disabled"
    target_label = "m2"
    priority = 30
    enabled = False

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        return False
