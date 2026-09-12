# ---------- Stage: builder ----------
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && pip install --no-cache-dir --prefix=/install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl \
    || python -m spacy download en_core_web_sm


# ---------- Stage: runtime ----------
FROM python:3.9-slim

WORKDIR /app

ENV NLTK_DATA=/usr/share/nltk_data \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /install /usr/local

COPY scripts/ ./scripts/
RUN python scripts/download_nltk.py

# مدل spaCy (اگر در builder نصب شده در site-packages باشد کافیست؛
# در غیر این صورت دوباره تلاش می‌کنیم)
RUN python -c "import spacy; spacy.load('en_core_web_sm')" \
    || python -m spacy download en_core_web_sm

COPY src/ ./src/
COPY Book1.xlsx ./

RUN mkdir -p /app/data/input /app/data/output

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.main"]
