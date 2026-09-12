"""
برچسب نقش حرف‌اضافه — بدون خراب کردن quantifier و infinitive.

- کلمه در preposition_set (Excel ∪ DEFAULT) یا of
- تک‌کلمه، غیرlocked
- برچسب ساختاری محافظت‌شده نباشد (m1/m3/m4/V)
→ role = preposition ، label خالی می‌ماند تا قوانین بعدی (مثلاً V+to)
  همچنان روی word='to' کار کنند.

of برای نقش preposition شناخته می‌شود ولی مرز NP نیست.
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import DEFAULT_PREPOSITIONS

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

_PROTECTED = {"m1", "m3", "m4", "V"}
# of مرز NP نیست ولی نقش حرف‌اضافه دارد
_ROLE_EXTRA = {"of"}


class PrepositionRule(Rule):
    name = "preposition_role"
    target_label = "special"
    priority = 87  # بعد از spaCy (86)، قبل از wordnet_finalize (88)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        preps = set(getattr(ctx, "preposition_set", None) or DEFAULT_PREPOSITIONS)
        preps |= _ROLE_EXTRA
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

            if tok.role != "preposition":
                tok.role = "preposition"
                changed = True
            if tok.label not in ("",):
                if tok.label in ("N", "m2", "adv"):
                    tok.label = ""
                    changed = True

        return changed
