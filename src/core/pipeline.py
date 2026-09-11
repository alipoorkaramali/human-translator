import pandas as pd

from .processor import Processor
from .rule_base import RuleRegistry
from .importers.data_importer import build_context
from .importers.np_importer import import_np_rules
from .importers.vp_importer import import_vp_rules

from src.utils import (
    preprocess_text, tokenize_english, number_type,
    is_possessive_or_s,
)
from src.ht_token import Token


class Pipeline:
    # ترتیب اجرا: اول NP (m1..m5 + special) سپس VP (vp1..vp3 + special)
    PHASES = [
        'm1', 'm2', 'm3', 'm4', 'm5', 'special',
        'vp1', 'vp2', 'vp3', 'vp_special',
    ]

    def __init__(self, excel_file: str = 'Book1.xlsx',
                 nltk_data_path: str = None):
        self.ctx = build_context(excel_file, nltk_data_path)
        self.registry = RuleRegistry()
        import_np_rules(self.registry)
        import_vp_rules(self.registry)
        self.processor = Processor(self.ctx, self.registry)

    def _initial_tokenize(self, text: str):
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

    def run(self, text: str, output_file: str = None) -> pd.DataFrame:
        self.processor.tokens = self._initial_tokenize(text)
        self.processor.run_all()

        df = self.processor.to_dataframe()
        if output_file:
            df.to_excel(output_file, index=False, engine='openpyxl')
        return df
