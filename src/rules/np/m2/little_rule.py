"""
قانون little / a little بر اساس countable / uncountable
(منطق هم‌تراز با نوت‌بوک):

  • فقط وقتی کلمهٔ بعدی برچسب N داشته باشد
  • "a little" (توکن مرکب یا a + little) → همیشه m1 + role quantifier
  • little + uncountable → m1 + determiner/quantifier
  • little + countable   → m2 + adjective
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import is_uncountable_noun

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class LittleRule(Rule):
    name = "little"
    target_label = "m2"
    priority = 30

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue

            current = tok.word.lower()
            # شامل "little" و توکن مرکب "a little"
            if "little" not in current:
                continue

            # فقط اگر کلمهٔ بعدی وجود داشته باشد و اسم (N) باشد
            if i + 1 >= len(tokens) or tokens[i + 1].label != "N":
                continue

            next_noun = tokens[i + 1].word

            # استثنا: "a little" به‌صورت یک توکن → همیشه quantifier
            if current == "a little":
                if tok.label != "m1" or tok.role != "determiner/quantifier":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True
                continue

            # الگوی جدا: a + little
            if (
                current == "little"
                and i >= 1
                and tokens[i - 1].word.lower() == "a"
                and not tokens[i - 1].locked
            ):
                prev = tokens[i - 1]
                if prev.label != "m1":
                    prev.label = "m1"
                    changed = True
                if tok.label != "m1" or tok.role != "determiner/quantifier":
                    tok.label = "m1"
                    tok.role = "determiner/quantifier"
                    changed = True
                continue

            # little به‌تنهایی
            if current == "little":
                if is_uncountable_noun(next_noun, ctx):
                    new_label, new_role = "m1", "determiner/quantifier"
                else:
                    new_label, new_role = "m2", "adjective"

                if tok.label != new_label or tok.role != new_role:
                    tok.label = new_label
                    tok.role = new_role
                    changed = True

        return changed
