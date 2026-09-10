from dataclasses import dataclass, field, replace


@dataclass
class Token:
    word: str
    label: str = ''          # m1..m5, N, V, adv, ''
    numtype: str = ''        # cardinal | ordinal | ''
    role: str = 'unknown'    # نقش از WordNet/dict
    locked: bool = False     # اگر True باشد، قوانین بعدی دست نمیزنند

    # 🆕 فیلدهای اضافه
    index: int = -1          # موقعیت در جمله (0-based)
    original: str = ''       # شکل اصلی قبل از نرمالسازی

    # ------------------------------------------------------------------
    def __post_init__(self):
        """اگر original خالی بود، با word مقداردهی شود."""
        if not self.original:
            self.original = self.word

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """خروجی سازگار با DataFrame فعلی (۴ ستون)."""
        return {
            'کلمه': self.word,
            'برچسب': self.label,
            'نوع_عدد': self.numtype,
            'نقش_از_دیکشنری': self.role,
        }

    # ------------------------------------------------------------------
    def copy(self, **overrides) -> 'Token':
        """
        کپی امن با امکان override کردن فیلدها.
        مثال:  t.copy(label='m4', locked=True)
        """
        return replace(self, **overrides)

    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        """آیا توکن واقعاً خالی است؟"""
        return not self.word.strip()

    # ------------------------------------------------------------------
    def reset_label(self) -> None:
        """برچسب و نقش را به حالت اولیه برگردان."""
        self.label = ''
        self.numtype = ''
        self.role = 'unknown'

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        """نمایش کوتاه برای دیباگ — بدون role برای خلوت بودن."""
        lock = '🔒' if self.locked else ''
        return f"Token({self.index}: '{self.word}' → {self.label or '∅'} {lock})"
