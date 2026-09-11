# =============================================================================
# src/core/pipeline.py - گردش کار کامل پردازش
#
# این ماژول:
#   1) Context را از Book1.xlsx + NLTK می‌سازد
#   2) چهار Importer را صدا می‌زند تا قوانین ثبت شوند
#   3) متن ورودی را پیش‌پردازش و توکنایز می‌کند
#   4) توکن‌های اولیه را به Processor می‌دهد
#   5) همهٔ فازها را اجرا می‌کند
#   6) DataFrame برمی‌گرداند
# =============================================================================
from typing import Optional

import pandas as pd

from ..token import Token                     # ← اصلاح شد (دو نقطه)
from ..utils import (
    preprocess_text, tokenize_english,
    number_type, is_possessive_or_s,
)
from .context import Context
from .processor import Processor
from .rule_base import RuleRegistry

# Importers — هر کدام ممکن است هنوز کامل نباشند، پس try/except
try:
    from .importers.data_importer import build_context
except ImportError:
    build_context = None

try:
    from .importers.m1_importer import import_m1_rules
except ImportError:
    import_m1_rules = None

try:
    from .importers.m2_m5_importer import import_m2_to_m5
except ImportError:
    import_m2_to_m5 = None

try:
    from .importers.special_checker import import_special_rules
except ImportError:
    import_special_rules = None


class Pipeline:
    """
    گردش کار کامل: از متن خام تا DataFrame.

    مثال:
        pipe = Pipeline(excel_file='Book1.xlsx')
        df = pipe.run("some books are here")
    """

    def __init__(self,
                 excel_file: str = 'Book1.xlsx',
                 nltk_data_path: Optional[str] = None):
        # 1) Context
        if build_context is None:
            raise ImportError(
                "data_importer آماده نیست. لطفاً "
                "src/core/importers/data_importer.py را بساز."
            )
        self.ctx = build_context(excel_file, nltk_data_path)

        # 2) Registry + Importerها
        self.registry = RuleRegistry()
        if import_m1_rules:
            import_m1_rules(self.registry)
        if import_m2_to_m5:
            import_m2_to_m5(self.registry)
        if import_special_rules:
            import_special_rules(self.registry)

        # 3) Processor
        self.processor = Processor(self.ctx, self.registry)

    # -------------------------------------------------------------------------
    # توکنایز اولیه (کپی ساده از منطق قدیمی — تا Ruleها آماده شوند)
    # -------------------------------------------------------------------------
    def _initial_tokenize(self, text: str):
        """
        متن خام را به لیست Token تبدیل می‌کند.
        این مرحله برچسب‌های ساده را می‌گذارد و Ruleها بعداً اصلاح می‌کنند.
        """
        text = preprocess_text(text)
        words = tokenize_english(text)

        tokens = []
        for i, w in enumerate(words):
            wl = w.lower()
            nt = number_type(w, self.ctx.cardinal_numbers,
                             self.ctx.ordinal_numbers) or ''

            if nt:
                tokens.append(Token(w, 'm1', nt, index=i))
            elif is_possessive_or_s(w):
                tokens.append(Token(w, 'm3', '', index=i))
            elif wl in self.ctx.intensifier_set:
                tokens.append(Token(w, 'adv', '', index=i))
            elif wl in self.ctx.phrases_set:
                tokens.append(Token(w, 'm1', '', index=i))
            else:
                tokens.append(Token(w, '', '', index=i))
        return tokens

    # -------------------------------------------------------------------------
    # اجرای کامل
    # -------------------------------------------------------------------------
    def run(self,
            text: str,
            output_file: Optional[str] = None) -> pd.DataFrame:
        """
        متن را کامل پردازش می‌کند.
        اگر output_file داده شود، خروجی در آن ذخیره می‌شود.
        """
        self.processor.tokens = self._initial_tokenize(text)
        self.processor.run_all()

        df = self.processor.to_dataframe()
        if output_file:
            df.to_excel(output_file, index=False, engine='openpyxl')
        return df

    # -------------------------------------------------------------------------
    # کمکی
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        n_rules = len(self.registry.all())
        return f"Pipeline(rules={n_rules})"
