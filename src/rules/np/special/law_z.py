"""
قانون ض (Law Z) — ادغام «صفت‌های مبهم + اسمِ جمعِ کمّی + of» در یک m1 چندکلمه‌ای.

مثال‌ها:
    large numbers of   → [large numbers of]=m1
    huge amounts of    → [huge amounts of]=m1
    various kinds of   → [various kinds of]=m1

شرایط اعمال (هم‌تراز با نسخهٔ نهایی نوت‌بوک، November 2025):
  ۱. هستهٔ عبارت یکی از اسم‌های جمعِ کمّی (plural_heads) باشد و بلافاصله بعدش «of» بیاید.
  ۲. حداقل یک modifier قبل از هسته باشد (m2 / adv / صفتِ WordNet / vague quantifier).
  ۳. در «کل NP جاری» هیچ ضمیر یا نشانهٔ ملکی نباشد
     (his large numbers of … → ممنوع). این همان اصلاح باگ possessive است.
  ۴. بین modifierها یک m1 «واقعی» (خارج از vague_quant_set، مثل the / two) نباشد
     (the large numbers of … → دست‌نخورده می‌ماند).
  ۵. کلمهٔ بعد از «of» فعل نباشد (kinds of running …).

بهبودها نسبت به نوت‌بوک:
  • کار با Token به‌جای سه لیست موازی؛ حفظ index و original.
  • احترام به توکن‌های locked.
  • هستهٔ جمع هرگز به‌عنوان مرز NP در نظر گرفته نمی‌شود
    (در نوت‌بوک «amounts» چون حس فعلی دارد، NP را قطع می‌کرد → رفتار ناسازگار).
  • تشخیص صفت با «هر حس a/s» در WordNet (نه فقط حس اول) به‌شرطی که حس اول فعل نباشد.
  • plural_heads از ctx.extra['law_z_plural_heads'] قابل توسعه است.
  • مقایسهٔ عبارات چندکلمه‌ای همیشه lower-case.
  • WordNet از ctx.wn گرفته می‌شود؛ اگر نبود، به‌صورت امن رد می‌شود (بدون crash).
"""
from typing import List, Optional, Set, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import is_np_boundary, is_possessive_or_s

if TYPE_CHECKING:
    from src.core.context import Context


DEFAULT_PLURAL_HEADS: Set[str] = {
    "numbers", "amounts", "kinds", "types", "sorts", "groups", "varieties",
    "bunches", "piles", "bits", "sets", "lots", "ranges", "series", "volumes",
    "heaps", "loads", "tons", "dozens", "scores", "myriads", "multitudes",
}


class LawZRule(Rule):
    name = "law_z"
    target_label = "special"
    priority = 81  # بعد از law_sh (80)، قبل از the_ordinal (82)

    # ------------------------------------------------------------------
    # کمکی‌ها
    # ------------------------------------------------------------------
    @staticmethod
    def _plural_heads(ctx: "Context") -> Set[str]:
        heads = set(DEFAULT_PLURAL_HEADS)
        extra = getattr(ctx, "extra", None) or {}
        more = extra.get("law_z_plural_heads") if hasattr(extra, "get") else None
        if more:
            heads |= {str(h).lower().strip() for h in more}
        return heads

    @staticmethod
    def _synsets(wn, word: str):
        if wn is None:
            return []
        try:
            return wn.synsets(word) or []
        except Exception:
            return []

    @classmethod
    def _is_adjective(cls, wn, word: str) -> bool:
        """صفت است اگر حس a/s داشته باشد و حس اول فعل نباشد."""
        syns = cls._synsets(wn, word)
        if not syns:
            return False
        if syns[0].pos() == "v":
            return False
        return any(s.pos() in ("a", "s") for s in syns)

    @classmethod
    def _first_sense_is_verb(cls, wn, word: str) -> bool:
        syns = cls._synsets(wn, word)
        return bool(syns) and syns[0].pos() == "v"

    @staticmethod
    def _np_end(tokens: List[Token], start: int, heads: Set[str]) -> int:
        """
        انتهای (exclusive) NP جاری از start.
        اولین توکن مرزی را هم شامل می‌کند (مثل نوت‌بوک)، اما هستهٔ جمع
        هرگز مرز حساب نمی‌شود.
        """
        j = start
        n = len(tokens)
        while j < n:
            tok = tokens[j]
            if tok.word.lower() not in heads and is_np_boundary(tok.word):
                return j + 1
            j += 1
        return n

    # ------------------------------------------------------------------
    # اعمال قانون
    # ------------------------------------------------------------------
    def apply(self, tokens: List[Token], ctx: "Context") -> bool:
        changed = False
        wn = getattr(ctx, "wn", None)
        vague: Set[str] = set(getattr(ctx, "vague_quant_set", set()) or set())
        heads = self._plural_heads(ctx)

        i = 0
        while i < len(tokens) - 1:
            start = i

            # ── مرحله ۱: مرز NP جاری ─────────────────────────────
            np_end = self._np_end(tokens, start, heads)

            # ── مرحله ۲: possessive در کل NP → قانون ممنوع ───────
            if any(is_possessive_or_s(tokens[j].word) or tokens[j].label == "m3"
                   for j in range(start, np_end)):
                i = max(np_end, start + 1)
                continue

            # ── مرحله ۳: پیمایش modifierها ───────────────────────
            modifier_end = start
            has_real_m1 = False
            blocked = False

            while modifier_end < len(tokens) - 1 and modifier_end < np_end:
                tok = tokens[modifier_end]
                if tok.locked:
                    blocked = True
                    break

                low = tok.word.lower()
                label = tok.label

                if label == "m1" and low not in vague:
                    has_real_m1 = True

                if label in ("m2", "adv", "m1"):
                    modifier_end += 1
                    continue
                if low in vague:
                    modifier_end += 1
                    continue
                if label == "" and self._is_adjective(wn, low):
                    modifier_end += 1
                    continue
                break

            if blocked:
                i = start + 1
                continue

            head_idx = modifier_end
            of_idx = head_idx + 1

            # ── مرحله ۴: هسته + of ───────────────────────────────
            if (head_idx >= len(tokens)
                    or of_idx >= len(tokens)
                    or tokens[head_idx].locked
                    or tokens[of_idx].locked
                    or tokens[head_idx].word.lower() not in heads
                    or tokens[of_idx].word.lower() != "of"):
                i = start + 1
                continue

            # ── مرحله ۵: کلمهٔ بعد از of فعل نباشد ────────────────
            if of_idx + 1 < len(tokens) and self._first_sense_is_verb(
                    wn, tokens[of_idx + 1].word.lower()):
                i = start + 1
                continue

            # بدون modifier → قانون ض معنا ندارد
            if modifier_end == start:
                i = start + 1
                continue

            # m1 واقعی (the / two / …) در modifierها → دست نزن، پرش بعد از of
            if has_real_m1:
                i = of_idx + 1
                continue

            # ── ادغام ────────────────────────────────────────────
            span = tokens[start:of_idx + 1]
            first = span[0]
            combined = Token(
                word=" ".join(t.word for t in span),
                label="m1",
                numtype="",
                role="quantifier_phrase (multi-word)",
                index=first.index,
                original=" ".join(t.original or t.word for t in span).strip(),
            )
            tokens[start:of_idx + 1] = [combined]
            changed = True
            i = start + 1

        return changed
