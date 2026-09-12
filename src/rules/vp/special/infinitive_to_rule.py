"""
قانون infinitive برای VP:

  ۱) فعل + to + فعل  → یک توکن V
       مثال: want to go  → "want to go"  (label=V, role=verb infinitive V+to+V)
       to اینجا رابط فعلی (infinitive marker) است.

  ۲) فعل + to         → یک توکن V
       مثال: want to     → "want to"     (label=V, role=verb infinitive V+to)
       فقط اگر بعد از to شروع NP نباشد (تا "go to school" خراب نشود).

اجرا بعد از spaCy (فاز vp_special) تا برچسب V آماده باشد.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context

# شروع محتمل گروه اسمی بعد از toی حرف‌اضافه (نه infinitive)
_NP_START_LABELS = {"N", "m1", "m2", "m3", "m4"}
_NP_START_WORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "my", "your", "his", "her", "its", "our", "their",
    "some", "any", "no", "every", "each", "all",
}


def _is_verb_tok(tok: "Token") -> bool:
    if tok.locked:
        return False
    if tok.label == "V":
        return True
    # گاهی AUX جدا مانده؛ spaCy معمولاً V زده
    return False


def _is_to(tok: "Token") -> bool:
    return (not tok.locked) and tok.word.lower() == "to"


def _looks_like_np_start(tok: "Token") -> bool:
    if tok.label in _NP_START_LABELS:
        return True
    if tok.word.lower() in _NP_START_WORDS:
        return True
    return False


class InfinitiveToRule(Rule):
    name = "infinitive_to"
    target_label = "vp_special"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        i = 0

        while i < len(tokens):
            # -------- الگوی بلندتر: V + to + V --------
            if (
                i + 2 < len(tokens)
                and _is_verb_tok(tokens[i])
                and _is_to(tokens[i + 1])
                and _is_verb_tok(tokens[i + 2])
            ):
                combined_word = (
                    f"{tokens[i].word} {tokens[i + 1].word} {tokens[i + 2].word}"
                )
                combined = Token(
                    word=combined_word,
                    label="V",
                    numtype="",
                    role="verb (infinitive: V+to+V; to=verb linker)",
                    index=tokens[i].index,
                    original=combined_word,
                    locked=False,
                )
                tokens[i : i + 3] = [combined]
                changed = True
                i += 1
                continue

            # -------- الگوی کوتاه‌تر: V + to (بدون NP بعدش) --------
            if (
                i + 1 < len(tokens)
                and _is_verb_tok(tokens[i])
                and _is_to(tokens[i + 1])
            ):
                # اگر بعد از to فعل است، الگوی سه‌تایی بالاتر باید گرفته باشد؛
                # اگر بعدش شبیه شروع NP است → to حرف اضافه است، ادغام نکن
                if i + 2 < len(tokens) and _looks_like_np_start(tokens[i + 2]):
                    i += 1
                    continue
                if i + 2 < len(tokens) and _is_verb_tok(tokens[i + 2]):
                    # باید با الگوی V+to+V گرفته می‌شد؛ رد
                    i += 1
                    continue

                combined_word = f"{tokens[i].word} {tokens[i + 1].word}"
                combined = Token(
                    word=combined_word,
                    label="V",
                    numtype="",
                    role="verb (infinitive: V+to)",
                    index=tokens[i].index,
                    original=combined_word,
                    locked=False,
                )
                tokens[i : i + 2] = [combined]
                changed = True
                i += 1
                continue

            i += 1

        return changed
