@{
    # باز کردن خودکار فایل Excel بعد از هر پردازش (watch)
    OpenExcel  = $false

    # باز کردن پوشه خروجی بعد از process.bat
    OpenFolder = $true

    # تأخیر debounce قبل از پردازش (میلی‌ثانیه)
    DebounceMs = 800

    # فاصله polling در watch (میلی‌ثانیه)
    PollMs     = 800

    # نوشتن لاگ در data/output/processor.log
    LogToFile  = $true

    # بعد از setup یک smoke test روی ایمیج اجرا شود
    SmokeTest  = $true
}
