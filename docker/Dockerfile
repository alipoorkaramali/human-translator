# ---------- Stage: builder (اختیاری، برای کاهش حجم) ----------
FROM python:3.9-slim AS builder

WORKDIR /app

# فقط requirements برای کش شدن بهتر لایه‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage: runtime ----------
FROM python:3.9-slim

WORKDIR /app

# 🆕 متغیرهای محیطی برای پایداری NLTK و جلوگیری از __pycache__
ENV NLTK_DATA=/usr/share/nltk_data \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# کپی پکیج‌های نصب‌شده از stage قبل
COPY --from=builder /install /usr/local

# 🆕 اضافه کردن omw-1.4 (برای wordnet 3.0+) + استخراج خودکار
RUN python -m nltk.downloader --dir=/usr/share/nltk_data \
        punkt wordnet cmudict omw-1.4 && \
    cd /usr/share/nltk_data/corpora && \
    if [ -f "wordnet.zip" ] && [ ! -d "wordnet" ]; then \
        python -c "import zipfile; zipfile.ZipFile('wordnet.zip').extractall('.')"; \
    fi

# 🆕 کپی کد (بازگشتی — شامل core/importers/rules/utils)
COPY src/ ./src/

# کپی فایل‌های جانبی
COPY Book1.xlsx ./

# 🆕 ساخت پوشه‌های لازم با مالکیت non-root
RUN mkdir -p /app/data/input /app/data/output

# 🆕 اجرا با کاربر غیر root (امنیت)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.main"]
