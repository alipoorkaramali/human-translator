"""
قوانین نهایی WordNet — بدون تداخل با TheOrdinal و MoreAfterM1Final.
"""
from typing import List, TYPE_CHECKING
import re

from src.core.rule_base import Rule
from src.utils import syllable_count, is_np_boundary

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_POS_ROLE = {
    "n": "noun", "v": "verb", "a": "adjective",
    "s": "adjective (satellite)", "r": "adverb",
}
_POS_LABEL = {"a": "m2", "s": "m2", "r": "adv", "n": "N", "v": "V"}
_LABEL_ROLE = {
    "m1": "determiner/quantifier", "m2": "adjective",
    "adv": "adverb", "N": "noun", "V": "verb", "": "function word",
}


class WordNetFinalizeRule(Rule):
    name = "wordnet_finalize"
    target_label = "special"
    priority = 88

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        wn = getattr(ctx, "wn", None)
        intensifiers = getattr(ctx, "intensifier_set", set()) or set()

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue
            w = tok.word
            label = tok.label
            is_multi = " " in w

            if is_multi and label == "m1":
                if tok.role != "quantifier_phrase (multi-word)":
                    tok.role = "quantifier_phrase (multi-word)"
                    changed = True
                continue

            if label == "m1" and tok.role in ("", "unknown"):
                tok.role = "determiner/quantifier"
                changed = True

            # ordinal را TheOrdinalRule مدیریت می‌کند — اینجا دست نزن
            if tok.numtype == "ordinal":
                continue

            if wn is None:
                continue

            try:
                syns = wn.synsets(w.lower())
            except Exception:
                syns = []

            if not syns:
                if tok.role in ("", "unknown"):
                    tok.role = "unknown"
                continue

            pos = syns[0].pos()
            new_role = _POS_ROLE.get(pos, "unknown")
            if tok.role in ("", "unknown"):
                tok.role = new_role
                changed = True
            elif tok.role in ("determiner/quantifier",) and label != "m1":
                tok.role = new_role
                changed = True

            if label in ("", "m2", "N", "V") and pos in _POS_LABEL:
                new_label = _POS_LABEL[pos]
                if tok.label != new_label:
                    tok.label = new_label
                    changed = True

        for tok in tokens:
            if tok.locked:
                continue
            if tok.word.lower() in intensifiers:
                if tok.label != "adv" or tok.role != "adverb (intensifier)":
                    tok.label = "adv"
                    tok.role = "adverb (intensifier)"
                    changed = True

        # more/most → adv فقط اگر m1 قبلش در NP نباشد
        for i in range(len(tokens) - 1):
            tok = tokens[i]
            if tok.locked or tok.word.lower() not in ("more", "most"):
                continue
            nxt = tokens[i + 1]
            if nxt.label != "m2" or syllable_count(nxt.word) <= 1:
                continue

            has_m1 = False
            j = i - 1
            while j >= 0:
                prev = tokens[j]
                if is_np_boundary(prev.word):
                    break
                if prev.label in ("m2", "adv") or prev.word.lower() in {",", "and", "but", "or"}:
                    break
                if prev.label == "m1":
                    has_m1 = True
                    break
                j -= 1

            if has_m1:
                continue  # MoreAfterM1Final مسئول است

            if tok.label != "adv" or tok.role != "adverb (comparative/superlative)":
                tok.label = "adv"
                tok.role = "adverb (comparative/superlative)"
                changed = True

        for tok in tokens:
            if tok.locked:
                continue
            lw = tok.word.lower()
            if lw == "of":
                if tok.label != "" or tok.role != "preposition":
                    tok.label = ""
                    tok.role = "preposition"
                    changed = True
            elif re.match(r"^[^\w\s]$", tok.word):
                if tok.role != "punctuation":
                    tok.role = "punctuation"
                    changed = True
            elif lw in {"a", "an", "the"}:
                if tok.role != "determiner/article":
                    tok.role = "determiner/article"
                    changed = True

            if tok.role in ("", "unknown"):
                tok.role = _LABEL_ROLE.get(tok.label, "unknown")
                changed = True

        return changed
