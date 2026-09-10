# ---------- Stage: builder ----------
FROM python:3.9-slim AS builder

WORKDIR /app

# نصب وابستگی‌ها در یک prefix جداگانه برای انتقال آسان
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------- Stage: runtime ----------
FROM python:3.9-slim

WORKDIR /app

# متغیرهای محیطی
ENV NLTK_DATA=/usr/share/nltk_data \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# انتقال پکیج‌های پایتون از builder
COPY --from=builder /install /usr/local

# 🆕 کپی اسکریپت دانلود NLTK و اجرای آن
COPY scripts/ ./scripts/
RUN python scripts/download_nltk.py

# کپی کد پروژه (بازگشتی: core, importers, rules, utils)
COPY src/ ./src/

# فایل‌های جانبی
COPY Book1.xlsx ./

# ساخت پوشه‌های لازم
RUN mkdir -p /app/data/input /app/data/output

# کاربر غیر root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.main"]
