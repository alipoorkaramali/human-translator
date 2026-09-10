FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی دیتای NLTK از پروژه
COPY nltk_data/ /usr/share/nltk_data/
ENV NLTK_DATA=/usr/share/nltk_data

# استخراج فایل‌های zip که NLTK نمی‌تونه مستقیم بخونه
RUN cd /usr/share/nltk_data/corpora && \
    if [ -f "wordnet.zip" ] && [ ! -d "wordnet" ]; then \
        python -c "import zipfile; zipfile.ZipFile('wordnet.zip').extractall('.')"; \
        echo '✅ wordnet استخراج شد'; \
    fi

COPY src/ ./src/
COPY Book1.xlsx ./

RUN mkdir -p /app/data/input /app/data/output

ENTRYPOINT ["python", "-m", "src.main"]