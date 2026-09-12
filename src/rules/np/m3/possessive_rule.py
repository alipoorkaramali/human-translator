"""
قانون ویژه: اسم + 's یا s' → برچسب N

مثال: students', children's, teachers', men's, Paris's

منطق نوت‌بوک:
  base = بدون پسوند ملکی
  اگر WordNet اسم بگوید → N
  وگرنه اگر m1 نبود → N
  (m1 دست‌نخورده می‌ماند)

ضمیرهای ملکی (my/his/…) از tokenize اولیه m3 می‌گیرند و اینجا تغییر نمی‌کنند.
"""
from typing import List, TYPE_CHECKING
import re

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_POSS_END = re.compile(r"['’]s$|s'$", re.I)


class PossessiveRule(Rule):
    name = "possessive"
    target_label = "m3"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        wn = getattr(ctx, "wn", None)

        for tok in tokens:
            if tok.locked:
                continue
            w = tok.word
            if not _POSS_END.search(w):
                continue

            # اگر از قبل m1 است دست نزن
            if tok.label == "m1":
                continue

            base = _POSS_END.sub("", w.lower())
            is_noun = False
            if wn is not None and base:
                try:
                    syns = wn.synsets(base)
                    if syns and any(s.pos() == "n" for s in syns):
                        is_noun = True
                    elif syns and syns[0].pos() == "n":
                        is_noun = True
                except Exception:
                    pass

            if is_noun or tok.label != "m1":
                if tok.label != "N":
                    tok.label = "N"
                    tok.role = "noun (possessive)"
                    changed = True

        return changed
