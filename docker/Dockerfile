FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# دانلود NLTK از اینترنت (توی CI کار می‌کنه چون گیت‌هاب فیلتر نیست)
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader --dir=/usr/share/nltk_data punkt wordnet cmudict

COPY src/ ./src/
COPY Book1.xlsx ./

RUN mkdir -p /app/data/input /app/data/output

ENTRYPOINT ["python", "-m", "src.main"]
