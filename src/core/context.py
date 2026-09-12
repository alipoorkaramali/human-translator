# =============================================================================
# src/core/context.py - نگه‌دارندهٔ مجموعه‌ها و دیکشنری‌ها
# =============================================================================
from dataclasses import dataclass, field
from typing import Set, Dict, Any


@dataclass
class Context:
    # مجموعه‌ها از Book1.xlsx (+ پیش‌فرض‌ها)
    phrases_set:      Set[str] = field(default_factory=set)
    cardinal_numbers: Set[str] = field(default_factory=set)
    ordinal_numbers:  Set[str] = field(default_factory=set)
    article_set:      Set[str] = field(default_factory=set)
    demotrative_set:  Set[str] = field(default_factory=set)
    simple_set:       Set[str] = field(default_factory=set)
    compound_set:     Set[str] = field(default_factory=set)
    intensifier_set:  Set[str] = field(default_factory=set)
    vague_quant_set:  Set[str] = field(default_factory=set)
    preposition_set:  Set[str] = field(default_factory=set)

    # دیکشنری‌های بارگذاری‌شده
    cmu: Dict[str, Any] = field(default_factory=dict)
    wn:  Any = None

    # محل ذخیرهٔ داده‌های جانبی
    extra: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def keys(self):
        return [
            'phrases_set', 'cardinal_numbers', 'ordinal_numbers',
            'article_set', 'demotrative_set', 'simple_set',
            'compound_set', 'intensifier_set', 'vague_quant_set',
            'preposition_set',
        ]

    def update_from_tuple(self, tup: tuple):
        """
        ترتیب tuple قدیمی (۹ تایی) — preposition جدا از Excel/default پر می‌شود.
        """
        (self.phrases_set, self.cardinal_numbers, self.ordinal_numbers,
         self.article_set, self.demotrative_set, self.simple_set,
         self.compound_set, self.intensifier_set, self.vague_quant_set) = tup
        return self
