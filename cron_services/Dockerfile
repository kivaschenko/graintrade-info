FROM python:3.12-slim 

WORKDIR /app

# Install cron and required packages
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create log file
RUN touch /var/log/cron.log

# Setup cron job
RUN echo "0 0 * * * /usr/local/bin/python /app/check_subscriptions.py >> /var/log/cron.log 2>&1" > /etc/cron.d/subscription-cron
RUN chmod 0644 /etc/cron.d/subscription-cron
RUN crontab /etc/cron.d/subscription-cron

# Start script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]