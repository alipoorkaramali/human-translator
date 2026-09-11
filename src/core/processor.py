# =============================================================================
# src/core/processor.py - موتور اجرای فازها روی توکن‌ها
#
# این ماژول:
#   - لیست توکن‌ها را نگه می‌دارد
#   - قوانین را به ترتیب فاز (m1..m5 + special) اجرا می‌کند
#   - هر فاز را تا ثبات (یا max_iter) تکرار می‌کند
#   - در انتها DataFrame می‌سازد
# =============================================================================
from typing import List, Optional

import pandas as pd

from ..ht_token import Token                    # ← اصلاح شد (دو نقطه)
from .context import Context                 # ← همان core/
from .rule_base import RuleRegistry          # ← همان core/


class Processor:
    """
    موتور اصلی: توکن‌ها را می‌گیرد و قوانین را روی آن‌ها اجرا می‌کند.
    """

    MAX_ITER_PER_PHASE = 5

    def __init__(self, ctx: Context, registry: RuleRegistry):
        self.ctx = ctx
        self.registry = registry
        self.tokens: List[Token] = []

    # ------------------------------------------------------------------
    def run_phase(self, phase: str) -> int:
        """
        اجرای همه قوانین یک فاز تا وقتی تغییری رخ ندهد
        یا به MAX_ITER برسد.
        برمی‌گرداند تعداد کل تغییرها.
        """
        rules = self.registry.by_label(phase)
        total_changes = 0

        for _ in range(self.MAX_ITER_PER_PHASE):
            phase_changed = False
            for rule in rules:
                if not rule.enabled:
                    continue
                changed = rule.apply(self.tokens, self.ctx)
                if changed:
                    phase_changed = True
                    total_changes += 1
            if not phase_changed:
                break

        return total_changes

    # ------------------------------------------------------------------
    def run_all(self) -> None:
        """اجرای همه فازها به ترتیب."""
        for phase in ['m1', 'm2', 'm3', 'm4', 'm5', 'special']:
            self.run_phase(phase)

    # ------------------------------------------------------------------
    def to_dataframe(self) -> pd.DataFrame:
        """تبدیل لیست توکن‌ها به DataFrame سازگار با خروجی قبلی."""
        rows = [t.to_dict() for t in self.tokens]
        return pd.DataFrame(rows)
