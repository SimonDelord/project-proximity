"""
BHP Proximity Truck Poller

Polls the Truck API at regular intervals and publishes
the truck data as JSON payloads to a Kafka topic.
"""

import os
import sys
import json
import time
import logging
import signal
from datetime import datetime
from typing import Optional

import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('truck-poller')

# Configuration from environment variables
TRUCK_API_URL = os.getenv('TRUCK_API_URL', 'http://localhost/trucks/sample')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'truck-telemetry')
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '10'))
KAFKA_CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'truck-poller')

# Optional Kafka security settings
KAFKA_SECURITY_PROTOCOL = os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')
KAFKA_SASL_MECHANISM = os.getenv('KAFKA_SASL_MECHANISM', None)
KAFKA_SASL_USERNAME = os.getenv('KAFKA_SASL_USERNAME', None)
KAFKA_SASL_PASSWORD = os.getenv('KAFKA_SASL_PASSWORD', None)

# Graceful shutdown flag
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False


def create_kafka_producer() -> Optional[KafkaProducer]:
    """Create and configure the Kafka producer."""
    try:
        config = {
            'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS.split(','),
            'client_id': KAFKA_CLIENT_ID,
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'acks': 'all',
            'retries': 3,
            'retry_backoff_ms': 1000,
        }

        # Add security configuration if specified
        if KAFKA_SECURITY_PROTOCOL != 'PLAINTEXT':
            config['security_protocol'] = KAFKA_SECURITY_PROTOCOL
            
        if KAFKA_SASL_MECHANISM:
            config['sasl_mechanism'] = KAFKA_SASL_MECHANISM
            config['sasl_plain_username'] = KAFKA_SASL_USERNAME
            config['sasl_plain_password'] = KAFKA_SASL_PASSWORD

        producer = KafkaProducer(**config)
        logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        return producer

    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return None


def fetch_truck_data() -> Optional[dict]:
    """Fetch truck data from the API."""
    try:
        response = requests.get(TRUCK_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Fetched truck data: {data.get('identification', {}).get('truck_id', 'unknown')}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch truck data from {TRUCK_API_URL}: {e}")
        return None


def publish_to_kafka(producer: KafkaProducer, data: dict) -> bool:
    """Publish truck data to Kafka topic."""
    try:
        # Use truck_id as the message key for partitioning
        truck_id = data.get('identification', {}).get('truck_id', 'unknown')
        
        # Add metadata to the payload
        payload = {
            'source': 'truck-poller',
            'polled_at': datetime.utcnow().isoformat(),
            'api_url': TRUCK_API_URL,
            'data': data
        }

        # Send message
        future = producer.send(
            topic=KAFKA_TOPIC,
            key=truck_id,
            value=payload
        )
        
        # Wait for confirmation
        record_metadata = future.get(timeout=10)
        
        logger.info(
            f"Published truck {truck_id} to {KAFKA_TOPIC} "
            f"[partition={record_metadata.partition}, offset={record_metadata.offset}]"
        )
        return True

    except KafkaError as e:
        logger.error(f"Failed to publish to Kafka: {e}")
        return False


def main():
    """Main polling loop."""
    global running

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 60)
    logger.info("BHP Proximity Truck Poller Starting")
    logger.info("=" * 60)
    logger.info(f"API URL: {TRUCK_API_URL}")
    logger.info(f"Kafka Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC}")
    logger.info(f"Poll Interval: {POLL_INTERVAL_SECONDS} seconds")
    logger.info("=" * 60)

    # Create Kafka producer
    producer = create_kafka_producer()
    if not producer:
        logger.error("Could not create Kafka producer, exiting")
        sys.exit(1)

    poll_count = 0
    success_count = 0
    error_count = 0

    try:
        while running:
            poll_count += 1
            logger.info(f"Poll #{poll_count} starting...")

            # Fetch truck data
            truck_data = fetch_truck_data()

            if truck_data:
                # Publish to Kafka
                if publish_to_kafka(producer, truck_data):
                    success_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1

            logger.info(
                f"Stats: polls={poll_count}, success={success_count}, errors={error_count}"
            )

            # Wait for next poll interval
            if running:
                logger.debug(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...")
                time.sleep(POLL_INTERVAL_SECONDS)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

    finally:
        # Cleanup
        if producer:
            logger.info("Flushing Kafka producer...")
            producer.flush(timeout=10)
            producer.close(timeout=10)
            logger.info("Kafka producer closed")

        logger.info(f"Final stats: polls={poll_count}, success={success_count}, errors={error_count}")
        logger.info("Truck Poller shutdown complete")


if __name__ == "__main__":
    main()

