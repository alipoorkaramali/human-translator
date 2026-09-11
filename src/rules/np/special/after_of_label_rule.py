"""
قانون ۳: بعد از of، کلمات بدون برچسب:
  - اگر در phrases_set → m1
  - وگرنه اگر WordNet اسم بگوید → N
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class AfterOfLabelRule(Rule):
    name = "after_of_label"
    target_label = "special"
    priority = 25

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        phrases = getattr(ctx, "phrases_set", set()) or set()
        wn = getattr(ctx, "wn", None)

        for i, tok in enumerate(tokens):
            if tok.word.lower() != "of":
                continue
            k = i + 1
            while k < len(tokens) and tokens[k].word.lower() != "of":
                t = tokens[k]
                if t.locked or t.label != "":
                    k += 1
                    continue
                w = t.word.lower()
                if w in phrases:
                    t.label = "m1"
                    changed = True
                elif wn is not None:
                    try:
                        syns = wn.synsets(w)
                        if syns and any(s.pos() == "n" for s in syns):
                            t.label = "N"
                            changed = True
                    except Exception:
                        pass
                k += 1
        return changed
