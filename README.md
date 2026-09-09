# Human Translator - Quantifier Tagger

یک ابزار خط فرمانی برای برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی با استفاده از NLTK و داکر.

## ویژگی‌ها
- برچسب‌زنی دقیق m1 (determiner/quantifier)، m2 (adjective)، adv، N، V و ...
- پشتیبانی از کسرها، اعداد مرکب، عبارات چندکلمه‌ای
- اجرای آفلاین با داکر (داده‌های NLTQ درون ایمیج)

## ساختار پروژه
- `src/`: کدهای اصلی (main.py و processor.py)
- `data/`: فایل‌های ورودی و خروجی
- `docker/`: فایل Dockerfile
- `Book1.xlsx`: مجموعه‌های کلمات (ضروری)

## نحوه اجرا با داکر

### ۱. ساخت ایمیج
```bash
docker build -f docker/Dockerfile -t text-processor .
