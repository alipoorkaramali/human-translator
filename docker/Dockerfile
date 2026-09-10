FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# دانلود NLTK + omw-1.4 (برای wordnet)
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader --dir=/usr/share/nltk_data punkt wordnet cmudict omw-1.4

# اطمینان از استخراج wordnet.zip
RUN cd /usr/share/nltk_data/corpora && \
    if [ -f "wordnet.zip" ] && [ ! -d "wordnet" ]; then \
        python -c "import zipfile; zipfile.ZipFile('wordnet.zip').extractall('.')"; \
    fi

COPY src/ ./src/
COPY Book1.xlsx ./

RUN mkdir -p /app/data/input /app/data/output

ENTRYPOINT ["python", "-m", "src.main"]
