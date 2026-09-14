"""
قوانین مرز گروه اسمی (NP boundary) — تنها منبع حقیقت.

ترتیب تشخیص در is_np_boundary:
  1) علائم نگارشی
  2) حروف اضافه (به‌جز of / as که هرگز مرز نیستند)
  3) حروف ربط
  4) EXTRA_NP_BOUNDARY_WORDS  ← لیست دستی تو
  5) فعل (برچسب V روی Token، یا WordNet pos=v)

برای گسترش: فقط EXTRA_NP_BOUNDARY_WORDS یا DEFAULT_PREPOSITIONS را عوض کن.
"""
from __future__ import annotations

import re
from typing import Any, Optional, Set

DEFAULT_PREPOSITIONS = {
    'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'about',
    'under', 'over', 'between', 'among', 'amongst', 'during', 'before',
    'after', 'since', 'until', 'till', 'into', 'onto', 'upon',
    'across', 'through', 'along', 'around', 'round', 'near', 'beside',
    'besides', 'behind', 'beyond', 'inside', 'outside', 'above', 'below',
    'beneath', 'within', 'without', 'against', 'toward', 'towards',
    'via', 'per', 'plus', 'minus', 'unlike', 'like', 'except', 'despite',
    'throughout', 'underneath', 'amid', 'amidst', 'atop',
    'up', 'down', 'off', 'out', 'past', 'next',
}

# of / as هرگز مرز NP نیستند
NEVER_NP_BOUNDARY_PREPS = frozenset({'of', 'as'})

NP_BOUNDARY_PUNCT = frozenset({
    '.', '!', '?', ';', ':', '—', ',', ')', ']', '}', '"', "'",
})

NP_BOUNDARY_CONJUNCTIONS = frozenset({
    'and', 'but', 'or', 'nor', 'yet', 'so',
})

# کلمات اضافه‌ای که خودت مرز می‌دانی — لیست را اینجا کامل کن
# مثال: EXTRA_NP_BOUNDARY_WORDS = {'however', 'therefore', 'meanwhile'}
EXTRA_NP_BOUNDARY_WORDS: Set[str] = set()


def is_np_boundary(token: Any, preposition_set: Optional[Set[str]] = None) -> bool:
    if not token:
        return False

    if hasattr(token, "label") and getattr(token, "label", "") == "V":
        return True

    t = str(token).lower()
    if hasattr(token, "word"):
        t = str(token.word).lower()

    if not t or " " in t:
        return False

    if t in NP_BOUNDARY_PUNCT or t[-1:] in {'.', '!', '?', ';', ':', '—'}:
        return True
    if re.search(r'[.!?;:—]$', t):
        return True

    if t in NEVER_NP_BOUNDARY_PREPS:
        return False

    preps = preposition_set if preposition_set is not None else DEFAULT_PREPOSITIONS
    if t in preps:
        return True

    if t in NP_BOUNDARY_CONJUNCTIONS:
        return True

    if t in EXTRA_NP_BOUNDARY_WORDS:
        return True

    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(t)
        if syns and syns[0].pos() == 'v':
            return True
    except Exception:
        pass
    return False
