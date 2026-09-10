from typing import List, Optional
import pandas as pd

from .token import Token
from .context import Context
from .rule_base import RuleRegistry


class Processor:
    PHASES = ['m1', 'm2', 'm3', 'm4', 'm5', 'special']

    def __init__(self, context: Context, registry: RuleRegistry):
        self.ctx = context
        self.registry = registry
        self.tokens: List[Token] = []

    # ------------------------- بارگذاری -------------------------
    def load(self, words, labels=None, numtypes=None):
        self.tokens = []
        for i, w in enumerate(words):
            lbl = labels[i]   if labels   and i < len(labels)   else ''
            nt  = numtypes[i] if numtypes and i < len(numtypes) else ''
            self.tokens.append(Token(word=w, label=lbl, numtype=nt))

    # ------------------------- اجرای یک فاز -------------------------
    def run_phase(self, phase: str, max_iter: int = 8) -> bool:
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

    # ------------------------- اجرای همه -------------------------
    def run_all(self, max_iter_per_phase: int = 8):
        for phase in self.PHASES:
            self.run_phase(phase, max_iter=max_iter_per_phase)

    # ------------------------- خروجی -------------------------
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([t.to_dict() for t in self.tokens])

    def save(self, path: str):
        self.to_dataframe().to_excel(path, index=False, engine='openpyxl')
