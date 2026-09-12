"""
تشخیص و ادغام تمام کسرها — نسخهٔ کامل نوت‌بوک.

شامل:
  2-1/2, two-thirds, one-half, twenty-three-hundredths,
  3/4, one third, one and a half, two and three quarters, ...

نتیجه: توکن ادغام‌شده با label=m1
numtype از روی آخرین بخش:
  one-third / 1/3 → cardinal
  twenty-third / 23rd → ordinal
"""
from typing import List, Optional, Tuple, TYPE_CHECKING
import re

from src.core.rule_base import Rule
from src.ht_token import Token

if TYPE_CHECKING:
    from src.core.context import Context

_EXCEPTIONS = {"ray", "level", "shaped", "term", "commerce", "known"}

_CARDINALS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred",
}
_FRACTIONS = {
    "half", "halves", "third", "thirds", "quarter", "quarters", "fourth", "fourths",
    "fifth", "fifths", "sixth", "seventh", "eighth", "ninth", "tenth",
}
_FRACTION_STEMS = {"half", "third", "quarter", "fourth"}


def _merge_at(words: List[str], i: int) -> Tuple[Optional[str], int, bool]:
    """همان منطق merge_fractions نوت‌بوک روی لیست str."""
    if i >= len(words):
        return None, i, False

    t = words[i]

    # 1. اسلشی ساده
    if re.match(r"^\d+/\d+$", t):
        return t, i + 1, True

    # 2. هیفن‌دار با ordinal ending
    if any(d in t for d in ("-", "‐", "–", "—")):
        clean_t = t.replace("‐", "-").replace("–", "-").replace("—", "-")
        parts = clean_t.split("-")
        last = parts[-1].lower()
        if any(
            last.rstrip("s").endswith(end)
            for end in ("th", "rd", "nd", "st", "half", "quarter", "third", "fourth")
        ):
            if last not in _EXCEPTIONS:
                return t, i + 1, True

    # 3. 2-1/2 style
    if re.match(r"^\d+[-‐–—]\d+/\d+$", t.replace(" ", "")):
        return t, i + 1, True

    # 4. 2 1/2 style
    if i + 1 < len(words) and words[i].isdigit() and re.match(r"^\d+/\d+$", words[i + 1]):
        return words[i] + "-" + words[i + 1], i + 2, True

    # 5. one half, three quarters, ...
    if i + 1 < len(words):
        w1, w2 = words[i].lower(), words[i + 1].lower()
        if w1 in _CARDINALS and w2 in _FRACTIONS:
            return words[i] + " " + words[i + 1], i + 2, True

    # 6. one and a half / two and three quarters
    if i + 3 < len(words) and words[i + 1].lower() == "and":
        if words[i + 2].lower() in {
            "a", "an", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"
        }:
            if words[i + 3].lower().rstrip("s") in _FRACTION_STEMS:
                return " ".join(words[i:i + 4]), i + 4, True

    # 7. one and one third / two and seven eighths
    if (
        i + 4 < len(words)
        and words[i + 1].lower() == "and"
        and words[i + 2].lower() in _CARDINALS
        and words[i + 4].lower().rstrip("s") in _FRACTIONS
    ):
        return " ".join(words[i:i + 5]), i + 5, True

    return None, i, False


def _fraction_numtype(merged: str, ordinal_numbers: set) -> str:
    """
    تشخیص نوع کسر از روی آخرین کلمه.
    one-third → cardinal | twenty-third → ordinal
    """
    last_part = merged.strip().replace("-", " ").split()[-1].lower()
    last_clean = re.sub(r"[.,]", "", last_part)

    if (
        last_clean in ordinal_numbers
        or re.match(r"^\d+(st|nd|rd|th)$", last_clean)
        or last_clean.endswith(("st", "nd", "rd", "th"))
    ):
        # کسرهای رایج مثل third/fourth که هم ordinal ending دارند ولی کسرند
        # فقط اگر دقیقاً الگوی 1st/2nd یا در ordinal_numbers اکسل باشد → ordinal
        # half/third/quarter به‌عنوان کسر → cardinal
        frac_words = {
            "half", "halves", "third", "thirds", "quarter", "quarters",
            "fourth", "fourths", "fifth", "fifths", "sixth", "sixths",
            "seventh", "sevenths", "eighth", "eighths", "ninth", "ninths",
            "tenth", "tenths", "hundredth", "hundredths",
            "thousandth", "thousandths",
        }
        if last_clean in frac_words or last_clean.rstrip("s") in {
            "half", "third", "quarter", "fourth", "fifth", "sixth",
            "seventh", "eighth", "ninth", "tenth", "hundredth", "thousandth",
        }:
            return "cardinal"
        return "ordinal"
    return "cardinal"


class FractionRule(Rule):
    name = "fraction"
    target_label = "m1"
    priority = 5  # خیلی زود — قبل از بقیهٔ m1

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()
        i = 0
        while i < len(tokens):
            if tokens[i].locked:
                i += 1
                continue

            words = [t.word for t in tokens]
            merged, next_i, ok = _merge_at(words, i)
            if not ok or next_i <= i:
                i += 1
                continue

            frac_type = _fraction_numtype(merged, ordinals)

            if next_i == i + 1:
                tok = tokens[i]
                if tok.label != "m1" or tok.numtype != frac_type:
                    tok.label = "m1"
                    tok.numtype = frac_type
                    tok.role = "fraction"
                    changed = True
                i = next_i
                continue

            combined = Token(
                word=merged,
                label="m1",
                numtype=frac_type,
                role="fraction",
                index=tokens[i].index,
                original=merged,
            )
            tokens[i:next_i] = [combined]
            changed = True
            i += 1

        return changed
