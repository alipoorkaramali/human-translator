# اجرای آفلاین روی ویندوز

با **Docker Desktop** بعد از یک‌بار ساخت ایمیج، بدون اینترنت پردازش کن.

## داشبورد گرافیکی (پیشنهادی)

دوبار کلیک روی **`start.bat`**

- تم تیره، دکمه‌های Setup / Watch / Process
- وضعیت Docker و ایمیج در نوار پایین
- باز کردن پوشه ورودی/خروجی و لاگ
- گزینه «باز کردن Excel»

نیازی به نصب برنامه اضافه نیست (WinForms داخلی ویندوز).

---

## پیش‌نیاز

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) روشن باشد  
2. `Book1.xlsx` در ریشه پروژه  
3. `nltk_data` (اگر نبود، setup با Python دانلود می‌کند)

## بار اول

```text
دوبار کلیک → start.bat  ← سپس Setup
```

## پردازش خودکار با Save

1. **`watch.bat`** را باز بگذار (یا از GUI دکمه **Watch (auto on Save)**)
2. هر فایل `.txt` را در `data\input` **ذخیره (Ctrl+S)** کن
3. خودکار پردازش می‌شود → `data\output\output_<نام>.xlsx`

نیازی به کلیک Process برای هر فایل نیست.

```bat
watch.bat                  # فقط فایل‌های جدید/تغییریافته
watch.bat -ProcessExisting # + فایل‌هایی که از قبل در input هستند
watch.bat -OpenExcel       # بعد از هر پردازش Excel را باز کن
```

## استفاده دستی

| فایل | کار |
|------|-----|
| **start.bat** | داشبورد گرافیکی |
| **watch.bat** | رصد خودکار input |
| **process.bat** | یک‌بار همه فایل‌های input |

خروجی: `data\output\output_<نام>.xlsx`  
لاگ: `data\output\processor.log`

## تغییر قوانین بدون rebuild

| میزبان | داخل کانتینر |
|--------|----------------|
| `src/` | `/app/src` |
| `Book1.xlsx` | `/app/Book1.xlsx` |
| `data/` | `/app/data` |

قانون یا اکسل را عوض کن → Save → Process/Watch بعدی همان را می‌بیند.  
فقط برای تغییر `requirements` / NLTK / spaCy → `setup.ps1 -Rebuild`.

## پیکربندی (`scripts/windows-config.psd1`)

| کلید | پیش‌فرض | معنی |
|------|---------|------|
| OpenExcel | false | باز کردن Excel بعد از پردازش |
| OpenFolder | true | باز کردن پوشه خروجی بعد از process |
| DebounceMs | 900 | صبر بعد از Save تا ادیتور نوشتن را تمام کند |
| PollMs | 1000 | پشتیبان polling |
| ProcessExistingOnStart | false | در شروع watch فایل‌های موجود را هم پردازش کن |
| SmokeTest | true | تست بعد از setup |

## اگر PowerShell خطا داد

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
