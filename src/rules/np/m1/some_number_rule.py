"""
قانون قطعی: some + عدد → adv

فقط وقتی some به‌تنهایی قبل از عدد باشد.
استثنا (m1 می‌ماند / دست‌نخورده):
  some hundred(s), some thousand(s), some dozen(s), some score
  و هر compound که با 'some ' شروع شود و در compound_set باشد.

باید زود اجرا شود (priority پایین).
"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule
from src.utils import number_type

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

# الگوهای compound که some در آن‌ها quantifier می‌ماند
_COMPOUND_PREFIXES = (
    "some hundred",
    "some thousand",
    "some dozen",
    "some score",
)
_COMPOUND_PHRASES = (
    "some hundreds",
    "some thousands",
    "some dozens",
)


class SomeNumberRule(Rule):
    name = "some_number"
    target_label = "m1"
    priority = 10  # اول از همه در فاز m1

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        n = len(tokens)
        cardinals = getattr(ctx, "cardinal_numbers", set()) or set()
        ordinals = getattr(ctx, "ordinal_numbers", set()) or set()
        compound_set = getattr(ctx, "compound_set", set()) or set()

        for i in range(n - 1):
            tok = tokens[i]
            if tok.locked:
                continue
            if tok.word.lower() != "some":
                continue
            if tok.label == "adv":
                continue

            nxt = tokens[i + 1]
            # آیا کلمهٔ بعدی عدد است؟
            nt = nxt.numtype or number_type(nxt.word, cardinals, ordinals)
            if not nt:
                continue

            # lookahead تا ۶ توکن برای تشخیص compound quantifier
            lookahead = " ".join(t.word for t in tokens[i:min(i + 6, n)]).lower()

            # استثنا ۱: الگوهای ثابت hundred/thousand/dozen/score
            if any(lookahead.startswith(p) for p in _COMPOUND_PREFIXES):
                continue
            if any(p in lookahead for p in _COMPOUND_PHRASES):
                continue

            # استثنا ۲: هر compound در اکسل که با 'some ' شروع شود
            if any(
                comp.startswith("some ") and comp in lookahead
                for comp in compound_set
            ):
                continue

            # some واقعاً به‌تنهایی قبل از عدد → adv
            tok.label = "adv"
            changed = True

        return changed
