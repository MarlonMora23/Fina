FROM python:3.12-slim as base

WORKDIR /app
COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*
COPY . .
USER chatpyme
ENV ENV=production
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]