import pandas as pd

from .processor import Processor
from .rule_base import RuleRegistry
from .importers.data_importer import build_context
from .importers.np_importer import import_np_rules
from .importers.vp_importer import import_vp_rules

from src.utils import (
    preprocess_text, tokenize_english, number_type,
    is_possessive_adjective, is_possessive_pronoun,
)
from src.ht_token import Token


class Pipeline:
    PHASES = [
        'm1', 'm2', 'm3', 'm4', 'm5', 'special',
        'vp1', 'vp2', 'vp3', 'vp_special',
        'np_span',
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
        poss_set = getattr(self.ctx, 'possessive_set', set()) or set()
        poss_pron_set = getattr(self.ctx, 'possessive_pronoun_set', set()) or set()
        for i, w in enumerate(words):
            wl = w.lower()

            if wl in poss_pron_set or is_possessive_pronoun(w):
                tokens.append(Token(
                    w, 'm1', 'possessive pronoun',
                    role='pronoun/possessive', index=i,
                ))
                continue

            if wl in poss_set or is_possessive_adjective(w):
                tokens.append(Token(
                    w, 'm1', 'possessive adj',
                    role='determiner/possessive', index=i,
                ))
                continue

            nt = number_type(w, self.ctx.cardinal_numbers,
                             self.ctx.ordinal_numbers) or ''

            if nt:
                tokens.append(Token(w, 'm1', nt, index=i))
            elif wl in self.ctx.intensifier_set:
                tokens.append(Token(w, 'adv', '', index=i))
            elif wl in self.ctx.article_set or wl in getattr(
                self.ctx, 'demotrative_set', set()
            ):
                tokens.append(Token(w, 'm1', '', index=i))
            elif wl in self.ctx.phrases_set:
                tokens.append(Token(w, 'm1', '', index=i))
            else:
                tokens.append(Token(w, '', '', index=i))
        return tokens

    def _record_seed_trace(self) -> None:
        """Remember seed labels as setters only — not listed as conflicts."""
        tr = self.processor.tracer
        tr.clear()
        for i, tok in enumerate(self.processor.tokens):
            if tok.label:
                tr._last_setter[(i, "label")] = "seed"

    def run(self, text: str, output_file: str = None) -> pd.DataFrame:
        self.processor.tokens = self._initial_tokenize(text)
        self._record_seed_trace()
        self.processor.run_all()

        df = self.processor.to_dataframe()
        if output_file:
            df.to_excel(output_file, index=False, engine="openpyxl")
        return df

    def save_trace(
        self,
        path_txt: str,
        path_xlsx: str = None,
        source_name: str = "",
    ) -> None:
        """Write label/rule conflict audit for the last run()."""
        self.processor.save_trace(
            path_txt, path_xlsx=path_xlsx, source_name=source_name
        )
