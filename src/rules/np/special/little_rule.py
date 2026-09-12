"""
قانون little / a little — بعد از WordNet (وقتی N مشخص است).

  • a little → همیشه m1
  • little + uncountable noun → m1
  • little + countable noun → m2
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_uncountable_noun

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class LittleRule(Rule):
    name = "little"
    target_label = "special"
    priority = 90  # بعد از wordnet_finalize (88)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue

            current = tok.word.lower()
            if "little" not in current:
                continue

            if i + 1 >= len(tokens):
                continue

            nxt = tokens[i + 1]
            # بعد از WordNet: N یا هنوز بدون برچسب ولی اسم‌مانند
            if nxt.label not in ("N", "") or not nxt.word.isalpha():
                if nxt.label != "N":
                    continue

            next_noun = nxt.word

            if current == "a little":
                if tok.label != "m1" or tok.role != "determiner/quantifier":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True
                continue

            if (
                current == "little"
                and i >= 1
                and tokens[i - 1].word.lower() == "a"
                and not tokens[i - 1].locked
            ):
                prev = tokens[i - 1]
                if prev.label != "m1":
                    prev.label = "m1"
                    changed = True
                if tok.label != "m1" or tok.role != "determiner/quantifier":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True
                continue

            if current == "little":
                # اگر بعدی N نیست ولی alpha است، فقط وقتی N است یا WordNet اسم
                if nxt.label != "N":
                    wn = getattr(ctx, "wn", None)
                    is_n = False
                    if wn is not None:
                        try:
                            syns = wn.synsets(next_noun.lower())
                            is_n = bool(syns and any(s.pos() == "n" for s in syns))
                        except Exception:
                            pass
                    if not is_n:
                        continue

                if is_uncountable_noun(next_noun, ctx):
                    new_label, new_role = "m1", "determiner/quantifier"
                else:
                    new_label, new_role = "m2", "adjective"

                if tok.label != new_label or tok.role != new_role:
                    tok.label = new_label
                    tok.role = new_role
                    changed = True

        return changed
