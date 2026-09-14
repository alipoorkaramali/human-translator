# اجرای آفلاین روی ویندوز

با **Docker Desktop** بعد از یک‌بار ساخت ایمیج، بدون اینترنت پردازش کن.

## پیش‌نیاز

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) روشن باشد  
2. `Book1.xlsx` در ریشه پروژه  
3. `nltk_data` (اگر نبود، setup با Python دانلود می‌کند)

## بار اول

```text
دوبار کلیک → setup.bat
```

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
| **watch.bat** | رصد `data\input`؛ هر `.txt` جدید/تغییریافته → پردازش |
| **process.bat** | همه `.txt`ها را یک‌بار پردازش می‌کند |

خروجی: `data\output\output_<نام>.xlsx`  
لاگ: `data\output\processor.log`

### باز کردن Excel

پیش‌فرض **خاموش** است. برای روشن کردن:

```bat
watch.bat -OpenExcel
```

یا در `scripts\windows-config.psd1`:

```powershell
OpenExcel = $true
```

## پیکربندی

فایل: `scripts/windows-config.psd1`

| کلید | پیش‌فرض | معنی |
|------|---------|------|
| OpenExcel | false | باز کردن Excel بعد از پردازش |
| OpenFolder | true | باز کردن پوشه خروجی بعد از process |
| DebounceMs | 800 | صبر قبل از پردازش (جلوگیری از Save نصفه) |
| PollMs | 800 | فاصله بررسی پوشه |
| SmokeTest | true | تست بعد از setup |

## اگر PowerShell خطا داد

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## نکات حرفه‌ای

- قفل فایل (`.locks`) جلوی پردازش همزمان یک فایل را می‌گیرد  
- فایل‌های `~*` و خالی نادیده گرفته می‌شوند  
- مسیرها با `$PSScriptRoot` پرتابل‌اند  
- ایمیج فقط هنگام setup به اینترنت نیاز دارد؛ runtime آفلاین است  
