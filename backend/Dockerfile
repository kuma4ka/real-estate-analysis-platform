FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev cron && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Setup cron (must run as root; cron daemon itself drops privileges per crontab entry)
COPY cron/crontab /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron \
    && crontab /etc/cron.d/scraper-cron \
    && touch /var/log/cron.log

EXPOSE 5000

CMD ["python", "run.py"]