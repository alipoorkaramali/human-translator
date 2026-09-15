"""
لایهٔ span برای ساخت NP of NP — بدون تغییر برچسب توکن‌ها.

خروجی:
  NP_داخلی : NP_a (سمت چپ of) | NP_b (سمت راست of)
  NP_of_NP : G-np1, G-np2, … برای کل بازهٔ [NP_a][of][NP_b]

of داخل توکن چندکلمه‌ای (مثل "lots of") لینکر جدا نیست.
"""
from typing import List, Optional, Tuple, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_np_boundary, DEFAULT_PREPOSITIONS

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_NP_LABELS = {"m1", "m2", "m3", "m4", "N"}
_NP_SOFT = {"adv"}


def _is_of_linker(tok: "Token") -> bool:
    if " " in tok.word:
        return False
    return tok.word.lower() == "of"


def _is_np_material(tok: "Token", preps: set) -> bool:
    if not tok.word or not tok.word.strip():
        return False
    w = tok.word.lower()
    if " " in w and tok.label == "m1":
        return True
    if w == "of":
        return False
    if tok.label == "V":
        return False
    if tok.label in _NP_LABELS:
        return True
    if tok.label in _NP_SOFT:
        return True
    if w in preps:
        return False
    if is_np_boundary(tok, preps):
        return False
    if tok.label == "" and tok.role in (
        "noun", "proper noun", "determiner/article", "determiner/quantifier",
        "determiner",
    ):
        return True
    return False


def _expand_left(tokens: List["Token"], end_excl: int, preps: set) -> int:
    j = end_excl - 1
    if j < 0 or not _is_np_material(tokens[j], preps):
        return end_excl
    start = j
    j -= 1
    while j >= 0 and _is_np_material(tokens[j], preps):
        start = j
        j -= 1
    return start


def _expand_right(tokens: List["Token"], start: int, preps: set) -> int:
    n = len(tokens)
    if start >= n or not _is_np_material(tokens[start], preps):
        return start
    end = start + 1
    while end < n and _is_np_material(tokens[end], preps):
        end += 1
    return end


def _has_nominal_head(tokens: List["Token"], a: int, b: int) -> bool:
    for i in range(a, b):
        if tokens[i].label in {"N", "m1", "m3", "m4"}:
            return True
        if " " in tokens[i].word and tokens[i].label == "m1":
            return True
    return False


class NpOfNpSpanRule(Rule):
    name = "np_of_np_span"
    target_label = "np_span"
    priority = 10

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        if not tokens:
            return False

        preps = set(getattr(ctx, "preposition_set", None) or DEFAULT_PREPOSITIONS)

        for t in tokens:
            t.np_inner = ""
            t.np_of_np = ""

        group_id = 0
        i = 0
        changed = False
        used = set()

        while i < len(tokens):
            if i in used or not _is_of_linker(tokens[i]):
                i += 1
                continue

            left_end = i
            right_start = i + 1

            left_start = _expand_left(tokens, left_end, preps)
            right_end = _expand_right(tokens, right_start, preps)

            if left_start >= left_end or right_start >= right_end:
                i += 1
                continue
            if not _has_nominal_head(tokens, left_start, left_end):
                i += 1
                continue
            if not _has_nominal_head(tokens, right_start, right_end):
                i += 1
                continue
            if any(j in used for j in range(left_start, right_end)):
                i += 1
                continue

            group_id += 1
            gname = f"G-np{group_id}"

            for j in range(left_start, left_end):
                tokens[j].np_inner = "NP_a"
                tokens[j].np_of_np = gname
                used.add(j)

            tokens[i].np_inner = ""
            tokens[i].np_of_np = gname
            used.add(i)

            for j in range(right_start, right_end):
                tokens[j].np_inner = "NP_b"
                tokens[j].np_of_np = gname
                used.add(j)

            changed = True
            i = right_end

        return changed
