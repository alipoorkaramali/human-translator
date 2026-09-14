# افزودن قانون جدید

## خلاصه

1. فایل Python را در پوشهٔ فاز درست بگذار.
2. یک کلاس از `Rule` بساز.
3. ذخیره کن و دوباره پردازش کن.

**نیازی به** ویرایش importer، rebuild داکر، یا تغییر pipeline **نیست**  
(وقتی `src/` مثل حالت پیش‌فرض ویندوز/Makefile mount است).

## پوشه‌ها

| نوع | مسیر |
|-----|------|
| NP / m1 | `src/rules/np/m1/` |
| NP / m2 | `src/rules/np/m2/` |
| NP / m3 | `src/rules/np/m3/` |
| NP / m4 | `src/rules/np/m4/` |
| NP / m5 | `src/rules/np/m5/` |
| NP special | `src/rules/np/special/` |
| VP | `src/rules/vp/vp1/` … `vp3/` یا `special/` |

## اسکلت قانون

```python
from typing import List, TYPE_CHECKING
from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context


class MyRule(Rule):
    name = "my_rule"          # یکتا
    target_label = "m1"       # m1..m5 / special / vp...
    priority = 50             # کوچک‌تر = زودتر

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        # ...
        return changed
```

همهٔ کلاس‌های `Rule` در این پوشه‌ها **خودکار** ثبت می‌شوند.

## واژگان فقط

لیست کلمات → ستون‌های `Book1.xlsx` (بدون کد).

## آفلاین / آنلاین

| محیط | تغییر قانون کد |
|------|----------------|
| Windows (`windows\start.bat`) | mount زنده `src/` → فوری |
| Makefile / docker با `-v src` | فوری |
| ایمیج بدون mount `src/` | فقط بعد از rebuild |

## Rebuild لازم است اگر

- پکیج جدید در `requirements.txt`
- تغییر Dockerfile
