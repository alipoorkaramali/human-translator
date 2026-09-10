# Human Translator - Quantifier Tagger

یک ابزار خط فرمانی برای برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی با استفاده از NLTK و داکر.

## ویژگی‌ها
- برچسب‌زنی دقیق m1 (determiner/quantifier)، m2 (adjective)، adv، N، V و ...
- پشتیبانی از کسرها، اعداد مرکب، عبارات چندکلمه‌ای
- اجرای آفلاین با داکر (داده‌های NLTQ درون ایمیج)

## ساختار پروژه

- `src/core/` : هستهٔ سیستم (Token, Context, Rule, Processor, Pipeline)
- `src/core/importers/` : چهار واردکننده
  - `data_importer.py` → Book1.xlsx + NLTK
  - `m1_importer.py`   → قوانین m1
  - `m2_m5_importer.py` → قوانین m2 تا m5
  - `special_checker.py` → حالت‌های خاص
- `src/rules/` : پیاده‌سازی قوانین به‌صورت Rule Class
- `src/utils.py` : ابزارهای عمومی
- `data/` : ورودی/خروجی
- `docker/` : Dockerfile
- `Book1.xlsx` : مجموعه‌های کلمات
## نحوه اجرا با داکر

### ۱. ساخت ایمیج
```bash
docker build -f docker/Dockerfile -t text-processor .
