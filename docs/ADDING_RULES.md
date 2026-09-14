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
    name = "my_rule"
    target_label = "m1"
    priority = 50

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        changed = False
        # ...
        return changed
```

## مسیر برچسب‌گذاری (trace)

بعد از هر پردازش برای هر ورودی:

| فایل | محتوا |
|------|--------|
| `data/output/output_<name>_trace.txt` | مسیر خوانا: قوانین، SET/OVERRIDE، چندبار برچسب |
| `data/output/output_<name>_trace.xlsx` | شیت `events` + `per_token` |

در CI همان‌ها داخل آرتیفکت `output-python` و `output-docker` هستند.

## واژگان فقط

لیست کلمات → ستون‌های `Book1.xlsx`.

## آفلاین / آنلاین

| محیط | تغییر قانون |
|------|-------------|
| Windows GUI | فوری (`src` mount) |
| docker با `-v src` | فوری |
| ایمیج بدون mount | بعد از rebuild |
