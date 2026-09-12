"""
برچسب نقش حرف‌اضافه — بدون خراب کردن quantifier و infinitive.

- کلمه در preposition_set (Excel ∪ DEFAULT)
- تک‌کلمه، غیرlocked
- برچسب ساختاری محافظت‌شده نباشد (m1/m3/m4/V)
→ role = preposition ، label خالی می‌ماند تا قوانین بعدی (مثلاً V+to)
  همچنان روی word='to' کار کنند.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import DEFAULT_PREPOSITIONS

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_PROTECTED = {"m1", "m3", "m4", "V"}


class PrepositionRule(Rule):
    name = "preposition_role"
    target_label = "special"
    priority = 87  # بعد از spaCy (86)، قبل از wordnet_finalize (88)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        preps = getattr(ctx, "preposition_set", None) or DEFAULT_PREPOSITIONS
        changed = False

        for tok in tokens:
            if tok.locked:
                continue
            if " " in tok.word:
                continue
            if tok.label in _PROTECTED:
                continue

            w = tok.word.lower()
            if w not in preps:
                continue

            # label را خالی نگه می‌داریم (مرز NP از is_np_boundary می‌آید)
            if tok.role != "preposition":
                tok.role = "preposition"
                changed = True
            if tok.label not in ("",):
                # اگر spaCy چیزی زده بود که حرف‌اضافه نیست، برای تک‌prep خالی کن
                # مگر adv/m2 که ممکن است اشتباه باشد ولی of/to را تمیز می‌کنیم
                if tok.label in ("N", "m2", "adv"):
                    tok.label = ""
                    changed = True

        return changed
