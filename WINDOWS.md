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

یا مستقیم `setup.bat`.

چه کار می‌کند؟

- چک Docker / Book1 / nltk_data  
- ساخت ایمیج `text-processor` از `docker/Dockerfile.offline`  
- **Smoke test** خودکار روی یک جمله نمونه  

ساخت مجدد:

```bat
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Rebuild
```

## استفاده

| فایل | کار |
|------|-----|
| **start.bat** | داشبورد گرافیکی (پیشنهادی) |
| **watch.bat** | رصد `data\input` در کنسول |
| **process.bat** | پردازش یک‌بار همه فایل‌ها |

خروجی: `data\output\output_<نام>.xlsx`  
لاگ: `data\output\processor.log`

### باز کردن Excel

در GUI با چک‌باکس، یا:

```bat
watch.bat -OpenExcel
```

یا در `scripts\windows-config.psd1`:

```powershell
OpenExcel = $true
```

## تغییر قوانین بدون rebuild

اسکریپت‌های ویندوز این مسیرها را **live mount** می‌کنند:

| میزبان | داخل کانتینر |
|--------|----------------|
| `src/` | `/app/src` |
| `Book1.xlsx` | `/app/Book1.xlsx` |
| `data/` | `/app/data` |

یعنی:

- قانون جدید در `src/rules/...` → ذخیره → **Process بعدی** همان کد را می‌بیند  
- کلمهٔ جدید در اکسل → **بدون** `setup -Rebuild`  
- فقط وقتی `requirements` / NLTK / spaCy عوض شد → **Rebuild**

## پیکربندی

فایل: `scripts/windows-config.psd1`

| کلید | پیش‌فرض | معنی |
|------|---------|------|
| OpenExcel | false | باز کردن Excel بعد از پردازش |
| OpenFolder | true | باز کردن پوشه خروجی بعد از process |
| DebounceMs | 800 | صبر قبل از پردازش |
| PollMs | 800 | فاصله بررسی پوشه |
| SmokeTest | true | تست بعد از setup |

## اگر PowerShell خطا داد

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## نکات حرفه‌ای

- قفل فایل (`.locks`) جلوی پردازش همزمان یک فایل را می‌گیرد  
- فایل‌های `~*` و خالی نادیده گرفته می‌شوند  
- مسیرها پرتابل‌اند  
- runtime بعد از setup آفلاین است  
- اگر `assets/app.ico` بگذاری، آیکون پنجره GUI عوض می‌شود  
