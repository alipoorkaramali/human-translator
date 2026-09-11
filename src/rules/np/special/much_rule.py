"""
قانون ۷–۸ نوت‌بوک برای much:
- much قبل از m2/adv → adv
- much قبل از کلمهٔ بدون برچسب که WordNet صفت/قید بگوید → adv
- much به‌تنهایی با برچسب خالی → adv
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class MuchRule(Rule):
    name = "much"
    target_label = "special"
    priority = 50

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        wn = getattr(ctx, "wn", None)

        for i, tok in enumerate(tokens):
            if tok.locked or tok.word.lower() != "much":
                continue

            # much به‌تنهایی
            if tok.label in ("", None):
                if i + 1 >= len(tokens):
                    tok.label = "adv"
                    changed = True
                    continue

            if i + 1 >= len(tokens):
                continue

            nxt = tokens[i + 1]
            if nxt.label in ("m2", "adv"):
                if tok.label != "adv":
                    tok.label = "adv"
                    changed = True
            elif tok.label in ("m1", "") and nxt.label == "" and wn is not None:
                try:
                    syns = wn.synsets(nxt.word.lower())
                    if syns and syns[0].pos() in ("a", "s", "r"):
                        tok.label = "adv"
                        changed = True
                except Exception:
                    pass

        # pass دوم: much خالی مانده
        for tok in tokens:
            if tok.locked:
                continue
            if tok.word.lower() == "much" and tok.label in ("", None):
                tok.label = "adv"
                changed = True

        return changed
