# BHP Proximity Truck Consumer Container
# Consumes truck telemetry from Kafka

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
COPY consumer.py .

# Default environment variables
ENV KAFKA_BOOTSTRAP_SERVERS=172.30.68.114:9092
ENV KAFKA_TOPIC=truck-telemetry
ENV KAFKA_CONSUMER_GROUP=truck-consumer-group
ENV KAFKA_CLIENT_ID=truck-consumer
ENV KAFKA_AUTO_OFFSET_RESET=earliest
ENV KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Run the consumer
CMD ["python", "consumer.py"]

