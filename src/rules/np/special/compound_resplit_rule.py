"""
قانون ۱: تفکیک مجدد compoundهایی که قبلاً m1 بودند ولی الان '' یا adv شدند.
مثال: "a lot of" → بعد از شکستن، بخش‌های quantifier دوباره m1 می‌گیرند.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import number_type
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context


class CompoundResplitRule(Rule):
    name = "compound_resplit"
    target_label = "special"
    priority = 10

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        phrases = getattr(ctx, "phrases_set", set()) or set()
        compounds = getattr(ctx, "compound_set", set()) or set()
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if " " in tok.word and tok.label in ("", "adv") and not tok.locked:
                parts = tok.word.split()
                new_tokens = []
                for j, p in enumerate(parts):
                    pl = p.lower()
                    pair = " ".join(parts[max(0, j - 1):j + 1]).lower()
                    if pl in phrases or pair in compounds:
                        lbl = "m1"
                    else:
                        lbl = ""
                    nt = number_type(p, cardinals, ordinals) or ""
                    new_tokens.append(
                        Token(word=p, label=lbl, numtype=nt, index=tok.index)
                    )
                tokens[i:i + 1] = new_tokens
                changed = True
                i += len(new_tokens)
            else:
                i += 1
        return changed
