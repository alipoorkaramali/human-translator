"""
قوانین جامع infinitive / semi-modal برای VP (از بلند به کوتاه).

پوشش اصلی:
  have/has/had got to (+V)
  would like/love/prefer/hate/want to (+V)
  be going/about/supposed/able/allowed/meant/forced/... to (+V)
  be to (+V)          — آیندهٔ رسمی: is to arrive
  have/has/had to (+V)
  need to / got to / used to / ought to / dare to (+V)
  V + to + V          — want to go, try to help, ...
  V + to              — فقط اگر بعدش NP نباشد

برچسب نهایی: V | to = رابط فعلی (verb linker)
"""
from typing import List, Tuple, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context

_BE = {"be", "am", "is", "are", "was", "were", "been", "being"}
_HAVE = {"have", "has", "had"}
_WOULD = {"would", "'d"}

# BE + mid + to [+ V]
_BE_TO_PATTERNS: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("going",), "be going to"),
    (("about",), "be about to"),
    (("supposed",), "be supposed to"),
    (("able",), "be able to"),
    (("unable",), "be unable to"),
    (("allowed",), "be allowed to"),
    (("meant",), "be meant to"),
    (("forced",), "be forced to"),
    (("required",), "be required to"),
    (("expected",), "be expected to"),
    (("prepared",), "be prepared to"),
    (("ready",), "be ready to"),
    (("willing",), "be willing to"),
    (("unwilling",), "be unwilling to"),
    (("eager",), "be eager to"),
    (("keen",), "be keen to"),
    (("happy",), "be happy to"),
    (("glad",), "be glad to"),
    (("reluctant",), "be reluctant to"),
    (("likely",), "be likely to"),
    (("unlikely",), "be unlikely to"),
    (("apt",), "be apt to"),
    (("due",), "be due to"),
    (("bound",), "be bound to"),
    (("set",), "be set to"),
    (("poised",), "be poised to"),
    (("liable",), "be liable to"),
    (("certain",), "be certain to"),
    (("sure",), "be sure to"),
)

# would + X + to [+ V]
_WOULD_TO_MIDS = {
    "like": "would like to",
    "love": "would love to",
    "prefer": "would prefer to",
    "hate": "would hate to",
    "want": "would want to",
}

# فعل‌های تک‌کلمه‌ای که تقریباً همیشه با to می‌آیند (حتی اگر برچسب هنوز V نباشد)
_FIXED_TO_HEADS = {
    "need": "need to",
    "ought": "ought to",
    "used": "used to",
    "dare": "dare to",
    "got": "got to",
}

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
    if end > len(tokens):
        return False
    for j in range(start, end):
        if tokens[j].locked:
            return False
    return True


def _merge(tokens: List["Token"], start: int, end: int, role: str) -> None:
    combined_word = " ".join(t.word for t in tokens[start:end])
    tokens[start:end] = [Token(
        word=combined_word,
        label="V",
        numtype="",
        role=role,
        index=tokens[start].index,
        original=combined_word,
        locked=False,
    )]


def _optional_following_v(
    tokens: List["Token"], end: int, base_role: str
) -> Tuple[int, str]:
    """اگر بعد از to فعل باشد، آن را هم داخل ادغام کن."""
    if end < len(tokens) and _is_verb_tok(tokens[end]):
        return end + 1, base_role.replace("; to=", "+V; to=")
    return end, base_role


class InfinitiveToRule(Rule):
    name = "infinitive_to"
    target_label = "vp_special"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        i = 0

        while i < len(tokens):
            # ----------------------------------------------------------
            # ۱) have/has/had + got + to [+ V]
            # ----------------------------------------------------------
            if (
                _w(tokens[i]) in _HAVE
                and not tokens[i].locked
                and i + 2 < len(tokens)
                and _w(tokens[i + 1]) == "got"
                and _is_to(tokens[i + 2])
                and _can_merge_range(tokens, i, i + 3)
            ):
                end = i + 3
                role = "verb (semi-modal: have got to; to=verb linker)"
                end, role = _optional_following_v(tokens, end, role)
                if end == i + 3 and end < len(tokens) and _looks_like_np_start(tokens[end]):
                    i += 1
                    continue
                _merge(tokens, i, end, role)
                changed = True
                i += 1
                continue

            # ----------------------------------------------------------
            # ۲) would + like|love|prefer|hate|want + to [+ V]
            # ----------------------------------------------------------
            if (
                _w(tokens[i]) in _WOULD
                and not tokens[i].locked
                and i + 2 < len(tokens)
                and _w(tokens[i + 1]) in _WOULD_TO_MIDS
                and _is_to(tokens[i + 2])
                and _can_merge_range(tokens, i, i + 3)
            ):
                name = _WOULD_TO_MIDS[_w(tokens[i + 1])]
                end = i + 3
                role = f"verb (semi-modal: {name}; to=verb linker)"
                end, role = _optional_following_v(tokens, end, role)
                _merge(tokens, i, end, role)
                changed = True
                i += 1
                continue

            # ----------------------------------------------------------
            # ۳) be + mid + to [+ V]
            # ----------------------------------------------------------
            if _w(tokens[i]) in _BE and not tokens[i].locked:
                matched = False
                for mid, name in _BE_TO_PATTERNS:
                    mid_len = len(mid)
                    need = 1 + mid_len + 1
                    if not _can_merge_range(tokens, i, i + need):
                        continue
                    if not all(_w(tokens[i + 1 + k]) == mid[k] for k in range(mid_len)):
                        continue
                    if not _is_to(tokens[i + 1 + mid_len]):
                        continue
                    end = i + need
                    role = f"verb (semi-modal: {name}; to=verb linker)"
                    end, role = _optional_following_v(tokens, end, role)
                    _merge(tokens, i, end, role)
                    changed = True
                    matched = True
                    i += 1
                    break
                if matched:
                    continue

                # be + to + V  (آیندهٔ رسمی: is to arrive)
                if (
                    i + 2 < len(tokens)
                    and _is_to(tokens[i + 1])
                    and _is_verb_tok(tokens[i + 2])
                    and _can_merge_range(tokens, i, i + 3)
                ):
                    _merge(
                        tokens,
                        i,
                        i + 3,
                        "verb (semi-modal: be to+V; to=verb linker)",
                    )
                    changed = True
                    i += 1
                    continue

            # ----------------------------------------------------------
            # ۴) have/has/had + to [+ V]
            # ----------------------------------------------------------
            if (
                _w(tokens[i]) in _HAVE
                and not tokens[i].locked
                and i + 1 < len(tokens)
                and _is_to(tokens[i + 1])
            ):
                end = i + 2
                role = "verb (semi-modal: have to; to=verb linker)"
                if end < len(tokens) and _is_verb_tok(tokens[end]):
                    end, role = _optional_following_v(tokens, end, role)
                elif end < len(tokens) and _looks_like_np_start(tokens[end]):
                    i += 1
                    continue
                if _can_merge_range(tokens, i, end):
                    _merge(tokens, i, end, role)
                    changed = True
                    i += 1
                    continue

            # ----------------------------------------------------------
            # ۵) need/ought/used/dare/got + to [+ V]
            # ----------------------------------------------------------
            head = _w(tokens[i])
            if (
                head in _FIXED_TO_HEADS
                and not tokens[i].locked
                and i + 1 < len(tokens)
                and _is_to(tokens[i + 1])
            ):
                name = _FIXED_TO_HEADS[head]
                end = i + 2
                role = f"verb (semi-modal: {name}; to=verb linker)"
                if end < len(tokens) and _is_verb_tok(tokens[end]):
                    end, role = _optional_following_v(tokens, end, role)
                elif end < len(tokens) and _looks_like_np_start(tokens[end]):
                    # used to the / got to the
                    i += 1
                    continue
                if _can_merge_range(tokens, i, end):
                    _merge(tokens, i, end, role)
                    changed = True
                    i += 1
                    continue

            # ----------------------------------------------------------
            # ۶) V + to + V  (infinitive عمومی)
            # ----------------------------------------------------------
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

            # ----------------------------------------------------------
            # ۷) V + to  (بدون NP بعدش)
            # ----------------------------------------------------------
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
