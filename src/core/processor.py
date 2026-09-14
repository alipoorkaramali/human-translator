# =============================================================================
# src/core/processor.py - موتور اجرای فازها روی توکن‌ها (+ label trace)
# =============================================================================
from typing import List, Optional

import pandas as pd

from ..ht_token import Token
from .context import Context
from .label_trace import LabelTracer
from .rule_base import RuleRegistry


class Processor:
    PHASES = [
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
        "special",
        "vp1",
        "vp2",
        "vp3",
        "vp_special",
        "np_span",
    ]

    def __init__(self, context: Context, registry: RuleRegistry):
        self.ctx = context
        self.registry = registry
        self.tokens: List[Token] = []
        self.tracer = LabelTracer()

    def load(
        self,
        words: List[str],
        labels: Optional[List[str]] = None,
        subtypes: Optional[List[str]] = None,
    ) -> None:
        labels = labels or [""] * len(words)
        subtypes = subtypes or [""] * len(words)
        self.tokens = []
        self.tracer.clear()
        for i, (w, lbl, nt) in enumerate(zip(words, labels, subtypes)):
            self.tokens.append(Token(word=w, label=lbl, subtype=nt, index=i))

    def run_phase(self, phase: str, max_iter: int = 8) -> bool:
        rules = self.registry.by_label(phase)
        any_change = False

        for _ in range(max_iter):
            changed_this_round = False
            for rule in rules:
                if not rule.enabled:
                    continue
                before = self.tracer.snapshot(self.tokens)
                applied = rule.apply(self.tokens, self.ctx)
                n = self.tracer.record_rule(
                    phase, rule.name, self.tokens, before
                )
                if applied or n > 0:
                    changed_this_round = True
                    any_change = True
            if not changed_this_round:
                break

        return any_change

    def run_all(self, max_iter_per_phase: int = 8) -> None:
        for phase in self.PHASES:
            iters = 1 if phase == "np_span" else max_iter_per_phase
            self.run_phase(phase, max_iter=iters)

    def run_rule(self, name: str, max_iter: int = 8) -> bool:
        rule = self.registry.by_name(name)
        any_change = False
        for _ in range(max_iter):
            before = self.tracer.snapshot(self.tokens)
            applied = rule.apply(self.tokens, self.ctx)
            n = self.tracer.record_rule(
                getattr(rule, "target_label", "") or "?",
                rule.name,
                self.tokens,
                before,
            )
            if not applied and n == 0:
                break
            any_change = True
        return any_change

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([t.to_dict() for t in self.tokens])

    def save(self, path: str = "data/output/output.xlsx") -> None:
        self.to_dataframe().to_excel(path, index=False, engine="openpyxl")

    def save_trace(
        self,
        path_txt: str,
        path_xlsx: Optional[str] = None,
        source_name: str = "",
    ) -> None:
        self.tracer.save(
            self.tokens,
            path_txt=path_txt,
            path_xlsx=path_xlsx,
            source_name=source_name,
        )
