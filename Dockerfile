FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOST=0.0.0.0
ENV PORT=5000
ENV FLASK_DEBUG=0
ENV MEMORY_BANK_DIR=/memory-bank
ENV LESSONS_DIR=/lessons-learned
ENV ADRS_DIR=/adrs
ENV FEATURES_DIR=/features

EXPOSE 5000

CMD ["python", "app.py"]
