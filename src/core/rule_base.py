from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.ht_token import Token
    from .context import Context


class Rule(ABC):
    name: str = "base"
    target_label: str = ""   # m1 / m2 / m3 / m4 / m5 / special
    priority: int = 100      # عدد کوچک‌تر = اجرای زودتر
    enabled: bool = True

    @abstractmethod
    def apply(self, tokens: List['Token'], ctx: 'Context') -> bool:
        """in-place تغییر می‌دهد و True برمی‌گرداند اگر تغییر کرده باشد."""
        ...


class RuleRegistry:
    def __init__(self):
        self._rules: List[Rule] = []

    def register(self, rule: Rule) -> Rule:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: (r.priority, r.name))
        return rule

    def all(self) -> List[Rule]:
        return list(self._rules)

    def by_label(self, label: str) -> List[Rule]:
        return [r for r in self._rules if r.target_label == label and r.enabled]

    def by_name(self, name: str) -> Rule:
        for r in self._rules:
            if r.name == name:
                return r
        raise KeyError(f"Rule '{name}' not found")
