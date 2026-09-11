# =============================================================================
# src/core/processor.py - موتور اجرای فازها روی توکن‌ها
#
# این ماژول:
#   - لیست توکن‌ها را نگه می‌دارد
#   - قوانین را به ترتیب فازهای NP و VP اجرا می‌کند
#   - هر فاز را تا ثبات (یا max_iter) تکرار می‌کند
#   - در انتها DataFrame می‌سازد
# =============================================================================
from typing import List, Optional

import pandas as pd

from ..ht_token import Token
from .context import Context
from .rule_base import RuleRegistry


class Processor:
    """
    موتور اصلی پردازش توکن‌ها.

    استفاده:
        proc = Processor(ctx, registry)
        proc.load(words, labels, numtypes)
        proc.run_all()
        df = proc.to_dataframe()
    """

    PHASES = [
        'm1', 'm2', 'm3', 'm4', 'm5', 'special',
        'vp1', 'vp2', 'vp3', 'vp_special',
    ]

    def __init__(self, context: Context, registry: RuleRegistry):
        self.ctx = context
        self.registry = registry
        self.tokens: List[Token] = []

    def load(self,
             words: List[str],
             labels: Optional[List[str]] = None,
             numtypes: Optional[List[str]] = None) -> None:
        """ساخت لیست Token از سه لیست موازی (سازگار با کد قدیمی)."""
        labels = labels or [''] * len(words)
        numtypes = numtypes or [''] * len(words)
        self.tokens = []
        for i, (w, lbl, nt) in enumerate(zip(words, labels, numtypes)):
            self.tokens.append(Token(word=w, label=lbl,
                                     numtype=nt, index=i))

    def run_phase(self, phase: str, max_iter: int = 8) -> bool:
        """
        اجرای همه قوانین یک فاز تا ثبات یا max_iter.
        برمی‌گرداند True اگر حداقل یک تغییر رخ داده باشد.
        """
        rules = self.registry.by_label(phase)
        any_change = False

        for _ in range(max_iter):
            changed_this_round = False
            for rule in rules:
                if not rule.enabled:
                    continue
                if rule.apply(self.tokens, self.ctx):
                    changed_this_round = True
                    any_change = True
            if not changed_this_round:
                break

        return any_change

    def run_all(self, max_iter_per_phase: int = 8) -> None:
        """اجرای همه فازها: NP (m1..m5 + special) سپس VP (vp1..vp3 + special)."""
        for phase in self.PHASES:
            self.run_phase(phase, max_iter=max_iter_per_phase)

    def run_rule(self, name: str, max_iter: int = 8) -> bool:
        """اجرای یک قانون خاص با نام."""
        rule = self.registry.by_name(name)
        any_change = False
        for _ in range(max_iter):
            if not rule.apply(self.tokens, self.ctx):
                break
            any_change = True
        return any_change

    def to_dataframe(self) -> pd.DataFrame:
        """تبدیل به DataFrame با ستون‌های استاندارد."""
        return pd.DataFrame([t.to_dict() for t in self.tokens])

    def save(self, path: str = 'data/output/output.xlsx') -> None:
        """ذخیره مستقیم در اکسل."""
        self.to_dataframe().to_excel(path, index=False, engine='openpyxl')

    def words(self) -> List[str]:
        return [t.word for t in self.tokens]

    def labels(self) -> List[str]:
        return [t.label for t in self.tokens]

    def numtypes(self) -> List[str]:
        return [t.numtype for t in self.tokens]
