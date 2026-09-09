# ۱. انتخاب تصویر پایه (سبک و کوچک)
FROM python:3.9-slim

# ۲. تعیین پوشهی کاری داخل کانتینر
WORKDIR /app

# ۳. کپی کردن فایل لیست کتابخانهها و نصب آنها
# (این کار جدا از کپی کد انجام میشود تا از کش داکر استفاده کنیم و build سریعتر شود)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ۴. تنظیم مسیر دادههای NLTK و دانلود آنها (اینجا با اینترنت دانلود میشود و داخل ایمیج قفل میگردد)
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader --dir=/usr/share/nltk_data punkt wordnet cmudict

# ۵. کپی کردن تمام کدهای اصلی برنامه (پوشه src) به داخل کانتینر
COPY src/ ./src/

# ۶. ایجاد پوشههای ورودی و خروجی در داخل کانتینر (تا هنگام Mount شدن دادهها مشکل نخوریم)
RUN mkdir -p /app/data/input /app/data/output

# ۷. مشخص کردن دستور اجرای پیشفرض هنگام شروع کانتینر
# -m یعنی ماژول؛ یعنی پایتون فایل src/main.py را اجرا کن
ENTRYPOINT ["python", "-m", "src.main"]
