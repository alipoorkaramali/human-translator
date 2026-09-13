from dataclasses import dataclass, replace


@dataclass
class Token:
    word: str
    label: str = ''          # m1..m5, N, V, adv, ''
    subtype: str = ''        # cardinal | ordinal | possessive adj | ''
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

    # سازگاری موقت با کد قدیمی که هنوز numtype می‌نویسد/می‌خواند
    @property
    def numtype(self) -> str:
        return self.subtype

    @numtype.setter
    def numtype(self, value: str) -> None:
        object.__setattr__(self, 'subtype', value or '')

    def to_dict(self) -> dict:
        return {
            'کلمه': self.word,
            'برچسب': self.label,
            'زیرنوع': self.subtype,
            'نقش_از_دیکشنری': self.role,
            'NP_داخلی': self.np_inner,
            'NP_of_NP': self.np_of_np,
        }

    def copy(self, **overrides) -> 'Token':
        if 'numtype' in overrides and 'subtype' not in overrides:
            overrides['subtype'] = overrides.pop('numtype')
        else:
            overrides.pop('numtype', None)
        return replace(self, **overrides)

    def is_empty(self) -> bool:
        return not self.word.strip()

    def reset_label(self) -> None:
        self.label = ''
        self.subtype = ''
        self.role = 'unknown'

    def __repr__(self) -> str:
        lock = '🔒' if self.locked else ''
        span = ''
        if self.np_of_np or self.np_inner:
            span = f' [{self.np_inner}|{self.np_of_np}]'
        st = f'/{self.subtype}' if self.subtype else ''
        return f"Token({self.index}: '{self.word}' → {self.label or '∅'}{st}{span} {lock})"


# dataclass __init__ را طوری بپیچ که numtype= به‌عنوان subtype پذیرفته شود
_token_init = Token.__init__


def _token_init_compat(self, *args, numtype=None, **kwargs):
    if numtype is not None and 'subtype' not in kwargs:
        kwargs['subtype'] = numtype
    return _token_init(self, *args, **kwargs)


Token.__init__ = _token_init_compat  # type: ignore[method-assign]
