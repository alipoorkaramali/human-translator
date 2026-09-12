"""
قانون ۴: اعداد مرکب معمولی (غیر کسری)

ادغام دنبالهٔ اعداد با and اختیاری.
نوع از روی آخرین جزء:
  twenty one          → cardinal + m1
  twenty first        → ordinal  + label خالی (برای the_ordinal بعدی)
"""
from typing import List, TYPE_CHECKING
import re

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import number_type, is_and_word

if TYPE_CHECKING:
    from src.core.context import Context

_ORDINAL_WORD_ENDS = (
    "st", "nd", "rd", "th",
    "first", "second", "third", "fourth", "fifth",
    "sixth", "seventh", "eighth", "ninth", "tenth",
    "eleventh", "twelfth",
)


class CompoundNumberRule(Rule):
    name = "compound_number"
    target_label = "m1"
    priority = 6  # بلافاصله بعد از fraction

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.locked:
                i += 1
                continue

            nt = tok.numtype or number_type(tok.word, cardinals, ordinals)
            if not nt:
                i += 1
                continue

            seq_indices = [i]
            j = i + 1
            while j < len(tokens):
                nxt = tokens[j]
                if nxt.locked:
                    break
                next_type = nxt.numtype or number_type(nxt.word, cardinals, ordinals)
                if next_type:
                    seq_indices.append(j)
                    j += 1
                    continue

                if is_and_word(nxt.word) and j + 1 < len(tokens):
                    nn = tokens[j + 1]
                    nn_type = nn.numtype or number_type(nn.word, cardinals, ordinals)
                    if nn_type and not nn.locked:
                        seq_indices.append(j)  # and
                        j += 1
                        continue
                break

            # فقط یک توکن → فقط برچسب/نوع را تنظیم کن
            if len(seq_indices) == 1:
                final_type = self._final_type(tok.word, ordinals)
                new_label = "m1" if final_type == "cardinal" else tok.label
                # برای ordinal تک‌کلمه، label را خالی نکن اگر قبلاً m1 از tokenize آمده
                # نوت‌بوک: ordinal → ''
                if final_type == "ordinal":
                    new_label = ""
                if tok.label != new_label or tok.numtype != final_type:
                    tok.label = new_label
                    tok.numtype = final_type
                    changed = True
                i = j
                continue

            # بررسی پیوستگی indices
            if seq_indices[-1] - seq_indices[0] + 1 != len(seq_indices):
                i += 1
                continue

            start, end = seq_indices[0], seq_indices[-1] + 1
            seq_words = [tokens[k].word for k in range(start, end)]
            combined_word = " ".join(seq_words)
            final_type = self._final_type(seq_words[-1], ordinals)
            new_label = "m1" if final_type == "cardinal" else ""

            combined = Token(
                word=combined_word,
                label=new_label,
                numtype=final_type,
                role="number",
                index=tokens[start].index,
                original=combined_word,
            )
            tokens[start:end] = [combined]
            changed = True
            i = start + 1

        return changed

    @staticmethod
    def _final_type(last_word: str, ordinal_numbers: set) -> str:
        last_clean = re.sub(r"[.,]", "", last_word.lower())
        if (
            last_clean in ordinal_numbers
            or re.match(r"^\d+(st|nd|rd|th)$", last_clean)
            or last_clean.endswith(_ORDINAL_WORD_ENDS)
        ):
            return "ordinal"
        return "cardinal"
