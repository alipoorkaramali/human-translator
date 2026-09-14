# Human Translator - Quantifier Tagger

یک ابزار خط فرمانی برای برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی با استفاده از NLTK و داکر.

## ویژگی‌ها
- برچسب‌زنی دقیق m1 (determiner/quantifier)، m2 (adjective)، adv، N، V و ...
- پشتیبانی از کسرها، اعداد مرکب، عبارات چندکلمه‌ای
- اجرای آفلاین با داکر (داده‌های NLTK درون ایمیج)

## ساختار پروژه

- `src/core/` : هستهٔ سیستم (Token, Context, Rule, Processor, Pipeline)
- `src/core/importers/` : واردکننده‌ها (Excel، قوانین NP/VP)
- `src/rules/` : پیاده‌سازی قوانین به‌صورت Rule Class
- `src/utils.py` : ابزارهای عمومی
- `data/` : ورودی/خروجی
- `docker/` : Dockerfile و Dockerfile.offline
- `scripts/` : setup/watch ویندوز + داشبورد GUI + دانلود NLTK
- `Book1.xlsx` : مجموعه‌های کلمات

## نحوه اجرا با داکر

### ۱. ساخت ایمیج (آنلاین / عادی)
```bash
docker build -f docker/Dockerfile -t text-processor .
```

### ۲. ساخت ایمیج آفلاین (NLTK داخل ایمیج)
```bash
docker build -f docker/Dockerfile.offline -t text-processor .
```

### ۳. اجرا
```bash
docker run --rm -v "$PWD/data:/app/data" -v "$PWD/Book1.xlsx:/app/Book1.xlsx" text-processor data/input/test.txt
```

## اجرای آفلاین روی ویندوز

دستورالعمل کامل: **[WINDOWS.md](WINDOWS.md)**

خلاصه:

1. **`start.bat`** — داشبورد گرافیکی (پیشنهادی)
2. یا `setup.bat` سپس `watch.bat` / `process.bat`
3. فایل `.txt` را در `data/input` بگذار → خروجی در `data/output`
