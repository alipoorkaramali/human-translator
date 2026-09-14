# اجرای آفلاین روی ویندوز

## یک پنجره کافی است

دوبار کلیک **`windows\start.bat`**:

| کنترل | رفتار |
|--------|--------|
| **Auto-watch** (پیش‌فرض روشن) | با Save هر `.txt` در `data\input` پردازش می‌شود |
| **Open Excel** | بعد از هر پردازش، اکسل جدید باز می‌شود |
| برداشتن تیک Auto-watch | watch خاموش می‌شود |

گزارش‌ها فقط در پنل Status رابط گرافیکی دیده می‌شوند (بدون پنجره CMD).

---

## بار اول

1. Docker Desktop روشن
2. `windows\start.bat` → **Setup (once)**
3. فایل را در `data\input` ذخیره کن

## لانچرها (فقط داخل `windows/`)

| فایل | کار |
|------|-----|
| `windows\start.bat` | GUI + auto-watch |
| `windows\setup.bat` | ساخت ایمیج |
| `windows\watch.bat` | watch کنسولی (اختیاری) |
| `windows\process.bat` | پردازش یک‌بار |

## قوانین بدون rebuild

`src/` و `Book1.xlsx` live mount هستند — تغییر قانون → Save → پردازش بعدی.
