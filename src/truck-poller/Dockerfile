# BHP Proximity Truck Poller Container
# Polls Truck API and publishes to Kafka

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY poller.py .

# Default environment variables (override at runtime)
ENV TRUCK_API_URL=https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
ENV KAFKA_BOOTSTRAP_SERVERS=172.30.68.114:9092
ENV KAFKA_TOPIC=truck-telemetry
ENV POLL_INTERVAL_SECONDS=10
ENV KAFKA_CLIENT_ID=truck-poller
ENV KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Run the poller
CMD ["python", "poller.py"]

