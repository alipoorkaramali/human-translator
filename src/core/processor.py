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

from ..token import Token                    # ← اصلاح شد (دو نقطه)
from .context import Context                 # ← همان core/
from .rule_base import RuleRegistry          # ← همان core/


class Processor:
    """
    موتور اصلی اجرای قوانین روی توکن‌ها.

    مثال:
        processor = Processor(ctx, registry)
        processor.load(words, labels, numtypes)
        processor.run_all()
        df = processor.to_dataframe()
    """

    # ترتیب اجرای فازها — همین ترتیب مهم است
    PHASES = ['m1', 'm2', 'm3', 'm4', 'm5', 'special']

    # -------------------------------------------------------------------------
    def __init__(self, context: Context, registry: RuleRegistry):
        self.ctx = context
        self.registry = registry
        self.tokens: List[Token] = []

    # -------------------------------------------------------------------------
    # بارگذاری توکن‌ها
    # -------------------------------------------------------------------------
    def load(self,
             words: List[str],
             labels: Optional[List[str]] = None,
             numtypes: Optional[List[str]] = None) -> None:
        """سه لیست موازی را به لیست Token تبدیل می‌کند."""
        self.tokens = []
        for i, w in enumerate(words):
            lbl = labels[i]   if labels   and i < len(labels)   else ''
            nt  = numtypes[i] if numtypes and i < len(numtypes) else ''
            self.tokens.append(Token(word=w, label=lbl,
                                     numtype=nt, index=i))

    # -------------------------------------------------------------------------
    # اجرای یک فاز مشخص تا ثبات
    # -------------------------------------------------------------------------
    def run_phase(self, phase: str, max_iter: int = 8) -> bool:
        """
        قوانین یک فاز را تا ثبات (یا max_iter) اجرا می‌کند.
        خروجی: True اگر حداقل یک تغییر رخ داده باشد.
        """
        rules = self.registry.by_label(phase)
        if not rules:
            return False

        any_change = False
        for _ in range(max_iter):
            changed = False
            for rule in rules:
                if rule.apply(self.tokens, self.ctx):
                    changed = True
            if not changed:
                break
            any_change = True
        return any_change

    # -------------------------------------------------------------------------
    # اجرای کل pipeline (m1 → m5 → special)
    # -------------------------------------------------------------------------
    def run_all(self, max_iter_per_phase: int = 8) -> None:
        """همهٔ فازها را به ترتیب اجرا می‌کند."""
        for phase in self.PHASES:
            self.run_phase(phase, max_iter=max_iter_per_phase)

    # -------------------------------------------------------------------------
    # اجرای یک قانون خاص (برای تست)
    # -------------------------------------------------------------------------
    def run_rule(self, name: str, max_iter: int = 8) -> bool:
        """یک Rule مشخص را با نام اجرا می‌کند."""
        rule = self.registry.by_name(name)
        any_change = False
        for _ in range(max_iter):
            if not rule.apply(self.tokens, self.ctx):
                break
            any_change = True
        return any_change

    # -------------------------------------------------------------------------
    # خروجی
    # -------------------------------------------------------------------------
    def to_dataframe(self) -> pd.DataFrame:
        """لیست Tokenها را به DataFrame تبدیل می‌کند."""
        return pd.DataFrame([t.to_dict() for t in self.tokens])

    def save(self, path: str = 'data/output/output.xlsx') -> None:
        """ذخیره خروجی در فایل اکسل."""
        self.to_dataframe().to_excel(path, index=False, engine='openpyxl')

    # -------------------------------------------------------------------------
    # کمک‌کننده‌ها (برای دسترسی قوانین)
    # -------------------------------------------------------------------------
    def words(self) -> List[str]:
        return [t.word for t in self.tokens]

    def labels(self) -> List[str]:
        return [t.label for t in self.tokens]

    def numtypes(self) -> List[str]:
        return [t.numtype for t in self.tokens]
