from dataclasses import dataclass

@dataclass
class Token:
    word: str
    label: str = ''          # m1..m5, N, V, adv, ''
    numtype: str = ''        # cardinal | ordinal | ''
    role: str = 'unknown'
    locked: bool = False     # اگر True باشد، قوانین بعدی دست نمی‌زنند

    def to_dict(self) -> dict:
        return {
            'کلمه': self.word,
            'برچسب': self.label,
            'نوع_عدد': self.numtype,
            'نقش_از_دیکشنری': self.role,
        }
