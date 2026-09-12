"""
قوانین infinitive و semi-modal برای VP — از بلند به کوتاه:

  be going to (+V)     am/is/are/was/were going to (leave)
  be about to (+V)
  be supposed to (+V)
  be able to (+V)
  be allowed to (+V)
  be meant to (+V)
  have/has/had to (+V)
  used to (+V)
  ought to (+V)
  V + to + V           want to go
  V + to               want to  (فقط اگر بعدش NP نباشد)

برچسب نهایی: V
نقش: توضیح نوع ساخت
to در این ساخت‌ها رابط فعلی (infinitive / semi-modal marker) است.
"""
from typing import List, Tuple, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context

_BE = {"be", "am", "is", "are", "was", "were", "been", "being"}
_HAVE = {"have", "has", "had"}

# الگو: BE + mid... + to  [+ V اختیاری]
_BE_TO_PATTERNS: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("going",), "be going to"),
    (("about",), "be about to"),
    (("supposed",), "be supposed to"),
    (("able",), "be able to"),
    (("allowed",), "be allowed to"),
    (("meant",), "be meant to"),
    (("ready",), "be ready to"),
    (("willing",), "be willing to"),
    (("likely",), "be likely to"),
    (("unlikely",), "be unlikely to"),
    (("due",), "be due to"),
    (("bound",), "be bound to"),
)

_NP_START_LABELS = {"N", "m1", "m2", "m3", "m4"}
_NP_START_WORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "my", "your", "his", "her", "its", "our", "their",
    "some", "any", "no", "every", "each", "all",
}


def _is_verb_tok(tok: "Token") -> bool:
    if tok.locked:
        return False
    return tok.label == "V"


def _is_to(tok: "Token") -> bool:
    return (not tok.locked) and tok.word.lower() == "to"


def _w(tok: "Token") -> str:
    return tok.word.lower()


def _looks_like_np_start(tok: "Token") -> bool:
    if tok.label in _NP_START_LABELS:
        return True
    if _w(tok) in _NP_START_WORDS:
        return True
    return False


def _can_merge_range(tokens: List["Token"], start: int, end: int) -> bool:
    """end exclusive — هیچ توکن locked نباشد."""
    if end > len(tokens):
        return False
    for j in range(start, end):
        if tokens[j].locked:
            return False
    return True


def _merge(
    tokens: List["Token"],
    start: int,
    end: int,
    role: str,
) -> None:
    combined_word = " ".join(t.word for t in tokens[start:end])
    combined = Token(
        word=combined_word,
        label="V",
        numtype="",
        role=role,
        index=tokens[start].index,
        original=combined_word,
        locked=False,
    )
    tokens[start:end] = [combined]


class InfinitiveToRule(Rule):
    name = "infinitive_to"
    target_label = "vp_special"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        i = 0

        while i < len(tokens):
            # ============================================================
            # ۱) be + (going|about|supposed|able|...) + to [+ V]
            # ============================================================
            if _w(tokens[i]) in _BE and not tokens[i].locked:
                matched = False
                for mid, name in _BE_TO_PATTERNS:
                    mid_len = len(mid)
                    need = 1 + mid_len + 1  # be + mid + to
                    if not _can_merge_range(tokens, i, i + need):
                        continue
                    ok_mid = all(
                        _w(tokens[i + 1 + k]) == mid[k] for k in range(mid_len)
                    )
                    if not ok_mid:
                        continue
                    if not _is_to(tokens[i + 1 + mid_len]):
                        continue

                    end = i + need
                    role = f"verb (semi-modal: {name}; to=verb linker)"
                    if end < len(tokens) and _is_verb_tok(tokens[end]):
                        end += 1
                        role = (
                            f"verb (semi-modal: {name}+V; to=verb linker)"
                        )

                    _merge(tokens, i, end, role)
                    changed = True
                    matched = True
                    i += 1
                    break
                if matched:
                    continue

            # ============================================================
            # ۲) have/has/had + to [+ V]
            # ============================================================
            if (
                _w(tokens[i]) in _HAVE
                and not tokens[i].locked
                and i + 1 < len(tokens)
                and _is_to(tokens[i + 1])
            ):
                end = i + 2
                role = "verb (semi-modal: have to; to=verb linker)"
                if end < len(tokens) and _is_verb_tok(tokens[end]):
                    end += 1
                    role = "verb (semi-modal: have to+V; to=verb linker)"
                elif end < len(tokens) and _looks_like_np_start(tokens[end]):
                    i += 1
                    continue
                if _can_merge_range(tokens, i, end):
                    _merge(tokens, i, end, role)
                    changed = True
                    i += 1
                    continue

            # ============================================================
            # ۳) used + to [+ V]
            # ============================================================
            if (
                _w(tokens[i]) == "used"
                and not tokens[i].locked
                and i + 1 < len(tokens)
                and _is_to(tokens[i + 1])
            ):
                end = i + 2
                role = "verb (semi-modal: used to; to=verb linker)"
                if end < len(tokens) and _is_verb_tok(tokens[end]):
                    end += 1
                    role = "verb (semi-modal: used to+V; to=verb linker)"
                elif end < len(tokens) and _looks_like_np_start(tokens[end]):
                    i += 1
                    continue
                if _can_merge_range(tokens, i, end):
                    _merge(tokens, i, end, role)
                    changed = True
                    i += 1
                    continue

            # ============================================================
            # ۴) ought + to [+ V]
            # ============================================================
            if (
                _w(tokens[i]) == "ought"
                and not tokens[i].locked
                and i + 1 < len(tokens)
                and _is_to(tokens[i + 1])
            ):
                end = i + 2
                role = "verb (semi-modal: ought to; to=verb linker)"
                if end < len(tokens) and _is_verb_tok(tokens[end]):
                    end += 1
                    role = "verb (semi-modal: ought to+V; to=verb linker)"
                if _can_merge_range(tokens, i, end):
                    _merge(tokens, i, end, role)
                    changed = True
                    i += 1
                    continue

            # ============================================================
            # ۵) V + to + V  (infinitive عمومی)
            # ============================================================
            if (
                i + 2 < len(tokens)
                and _is_verb_tok(tokens[i])
                and _is_to(tokens[i + 1])
                and _is_verb_tok(tokens[i + 2])
            ):
                _merge(
                    tokens,
                    i,
                    i + 3,
                    "verb (infinitive: V+to+V; to=verb linker)",
                )
                changed = True
                i += 1
                continue

            # ============================================================
            # ۶) V + to  (بدون NP بعدش)
            # ============================================================
            if (
                i + 1 < len(tokens)
                and _is_verb_tok(tokens[i])
                and _is_to(tokens[i + 1])
            ):
                if i + 2 < len(tokens) and _looks_like_np_start(tokens[i + 2]):
                    i += 1
                    continue
                if i + 2 < len(tokens) and _is_verb_tok(tokens[i + 2]):
                    i += 1
                    continue
                if _can_merge_range(tokens, i, i + 2):
                    _merge(
                        tokens,
                        i,
                        i + 2,
                        "verb (infinitive: V+to)",
                    )
                    changed = True
                    i += 1
                    continue

            i += 1

        return changed
