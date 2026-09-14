# اجرای آفلاین روی ویندوز

با **Docker Desktop** و اسکریپت‌های این مخزن می‌توانی بدون اینترنت (بعد از یک‌بار ساخت ایمیج) متن را پردازش کنی.

## پیش‌نیاز

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) نصب و در حال اجرا
2. `Book1.xlsx` در ریشه پروژه
3. پوشه `nltk_data` (اگر نبود، `setup` سعی می‌کند با Python دانلود کند)

## بار اول

دوبار کلیک روی **`setup.bat`**

- Docker را چک می‌کند
- در صورت نیاز `nltk_data` را می‌سازد
- ایمیج `text-processor` را از `docker/Dockerfile.offline` می‌سازد

ساخت مجدد ایمیج:

```bat
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Rebuild
```

## استفاده روزمره

| فایل | کار |
|------|-----|
| **watch.bat** | هر `.txt` در `data\input` را رصد و پردازش می‌کند؛ Excel را باز می‌کند |
| **process.bat** | همه فایل‌های `data\input` را یک‌بار پردازش می‌کند |

خروجی‌ها: `data\output\output_<نام‌فایل>.xlsx`

## اگر PowerShell خطا داد

یک‌بار در PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## نکات

- ایمیج فقط هنگام `setup` به اینترنت نیاز دارد (pip / spaCy). بعد از آن runtime آفلاین است.
- فایل‌های موقت Office (`~*`) نادیده گرفته می‌شوند.
- مسیرها با `$PSScriptRoot` پرتابل‌اند؛ هر جا clone کنی کار می‌کند.
