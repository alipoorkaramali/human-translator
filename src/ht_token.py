from dataclasses import dataclass, replace


@dataclass
class Token:
    word: str
    label: str = ''          # m1..m5, N, V, adv, ''
    numtype: str = ''        # cardinal | ordinal | ''
    role: str = 'unknown'    # نقش از WordNet/dict
    locked: bool = False     # اگر True باشد، قوانین بعدی دست نمیزنند

    index: int = -1          # موقعیت در جمله (0-based)
    original: str = ''       # شکل اصلی قبل از نرمالسازی

    # لایهٔ span (ستون‌های خروجی جدا — برچسب توکن را عوض نمی‌کنند)
    np_inner: str = ''       # NP_a | NP_b | …
    np_of_np: str = ''       # G-np1 | G-np2 | …

    def __post_init__(self):
        if not self.original:
            self.original = self.word

    def to_dict(self) -> dict:
        return {
            'کلمه': self.word,
            'برچسب': self.label,
            'نوع_عدد': self.numtype,
            'نقش_از_دیکشنری': self.role,
            'NP_داخلی': self.np_inner,
            'NP_of_NP': self.np_of_np,
        }

    def copy(self, **overrides) -> 'Token':
        return replace(self, **overrides)

    def is_empty(self) -> bool:
        return not self.word.strip()

    def reset_label(self) -> None:
        self.label = ''
        self.numtype = ''
        self.role = 'unknown'

    def __repr__(self) -> str:
        lock = '🔒' if self.locked else ''
        span = ''
        if self.np_of_np or self.np_inner:
            span = f' [{self.np_inner}|{self.np_of_np}]'
        return f"Token({self.index}: '{self.word}' → {self.label or '∅'}{span} {lock})"
