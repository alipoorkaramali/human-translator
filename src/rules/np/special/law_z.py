"""
قانون ض (Law Z) — نسخهٔ نهایی + اصلاح باگ possessive

اگر در یک NP:
  [modifiers بدون m1 واقعی] + plural_head + of
و در کل NP ضمیر/نشانهٔ ملکی نباشد،
آن محدوده ادغام می‌شود و برچسب m1 می‌گیرد.

مثال مفهومی: various kinds of → یک توکن m1
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import is_np_boundary, is_possessive_or_s

if TYPE_CHECKING:
    from src.core.context import Context

_PLURAL_HEADS = {
    "numbers", "amounts", "kinds", "types", "sorts", "groups", "varieties",
    "bunches", "piles", "bits", "sets", "lots", "ranges", "series", "volumes",
    "heaps", "loads", "tons", "dozens", "scores", "myriads", "multitudes",
}


class LawZRule(Rule):
    name = "law_z"
    target_label = "special"
    priority = 81

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        vague = getattr(ctx, "vague_quant_set", set()) or set()
        wn = getattr(ctx, "wn", None)

        i = 0
        while i < len(tokens) - 1:
            start = i

            # مرحله ۱: مرز NP جاری
            np_boundary = i
            while np_boundary < len(tokens):
                if is_np_boundary(tokens[np_boundary].word):
                    np_boundary += 1
                    break
                np_boundary += 1

            # مرحله ۲: اگر در این NP ملکی باشد → کل NP را رد کن
            possessive_in_np = any(
                is_possessive_or_s(tokens[j].word)
                for j in range(i, np_boundary)
            )
            if possessive_in_np:
                i = np_boundary
                continue

            # مرحله ۳: رد شدن از modifierها تا head
            modifier_end = i
            has_real_m1 = False

            while modifier_end < len(tokens) - 1 and modifier_end < np_boundary:
                tok = tokens[modifier_end]
                word_low = tok.word.lower()
                label = tok.label

                if label == "m1":
                    phrase = tok.word if " " in tok.word else word_low
                    if phrase not in vague:
                        has_real_m1 = True

                if label in ("m2", "adv"):
                    modifier_end += 1
                    continue
                if label == "" and wn is not None:
                    try:
                        syns = wn.synsets(word_low)
                        if syns and syns[0].pos() in ("a", "s"):
                            modifier_end += 1
                            continue
                    except Exception:
                        pass
                if word_low in vague:
                    modifier_end += 1
                    continue
                if label == "m1":
                    modifier_end += 1
                    continue
                break

            head_idx = modifier_end
            of_idx = modifier_end + 1

            if (
                head_idx >= len(tokens)
                or tokens[head_idx].word.lower() not in _PLURAL_HEADS
                or of_idx >= len(tokens)
                or tokens[of_idx].word.lower() != "of"
            ):
                i = start + 1
                continue

            # اگر بعد از of فعل باشد → رد
            if of_idx + 1 < len(tokens) and wn is not None:
                next_w = tokens[of_idx + 1].word.lower()
                try:
                    syns = wn.synsets(next_w)
                    if syns and syns[0].pos() == "v":
                        i = start + 1
                        continue
                except Exception:
                    pass

            if modifier_end == start:
                i = start + 1
                continue

            if has_real_m1:
                i = of_idx + 1
                continue

            # ادغام start .. of_idx → یک توکن m1
            combined_word = " ".join(t.word for t in tokens[start:of_idx + 1])
            combined = Token(
                word=combined_word,
                label="m1",
                numtype="",
                role="quantifier_phrase (multi-word)",
                index=tokens[start].index,
                original=combined_word,
            )
            tokens[start:of_idx + 1] = [combined]
            changed = True
            i = start + 1

        return changed
