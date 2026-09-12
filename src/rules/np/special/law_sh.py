"""
قانون ش (Law Sh) — بدون تغییر نسبت به نوت‌بوک

الگو: a/an + [modifiers] + singular_head + of
→ ادغام به یک توکن m1

اگر قبلش ملکی باشد (بدون punct قوی بینشان) → اجرا نمی‌شود.

مثال مفهومی: a number of → یک توکن m1
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.ht_token import Token
from src.utils import possessive_before_index

if TYPE_CHECKING:
    from src.core.context import Context

_SINGULAR_HEADS = {
    "number", "amount", "kind", "type", "sort", "deal", "pile", "bunch", "bit",
    "set", "group", "variety", "lot", "sum", "many", "quantity",
}


class LawShRule(Rule):
    name = "law_sh"
    target_label = "special"
    priority = 80

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        vague = getattr(ctx, "vague_quant_set", set()) or set()
        wn = getattr(ctx, "wn", None)

        i = 0
        while i < len(tokens) - 2:
            # اگر possessive قبلش باشد → رد
            if possessive_before_index(tokens, i, max_lookback=15):
                i += 1
                continue

            if tokens[i].word.lower() not in {"a", "an"}:
                i += 1
                continue

            if tokens[i].locked:
                i += 1
                continue

            start = i
            k = i + 1

            while k < len(tokens):
                tok = tokens[k]
                word = tok.word.lower()
                label = tok.label

                if label in ("m2", "adv"):
                    k += 1
                    continue
                if label == "" and wn is not None:
                    try:
                        syns = wn.synsets(word)
                        if syns and syns[0].pos() in ("a", "s"):
                            k += 1
                            continue
                    except Exception:
                        pass
                if word in vague:
                    k += 1
                    continue
                break

            if (
                k < len(tokens)
                and tokens[k].word.lower() in _SINGULAR_HEADS
                and k + 1 < len(tokens)
                and tokens[k + 1].word.lower() == "of"
            ):
                combined_word = " ".join(t.word for t in tokens[start:k + 2])
                combined = Token(
                    word=combined_word,
                    label="m1",
                    numtype="",
                    role="quantifier_phrase (multi-word)",
                    index=tokens[start].index,
                    original=combined_word,
                )
                tokens[start:k + 2] = [combined]
                changed = True
                i = start + 1
            else:
                i += 1

        return changed
