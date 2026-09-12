"""مقاله a/an/the → m1"""
from typing import List, TYPE_CHECKING

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class ArticleRule(Rule):
    name = "article"
    target_label = "m1"
    priority = 20

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        articles = getattr(ctx, "article_set", set()) or {"a", "an", "the"}

        for tok in tokens:
            if tok.locked:
                continue
            if tok.word.lower() in articles:
                if tok.label != "m1":
                    tok.label = "m1"
                    tok.role = "determiner/article"
                    changed = True
        return changed
