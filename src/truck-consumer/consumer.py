"""
BHP Proximity Truck Consumer

Consumes truck telemetry data from a Kafka topic
and logs/processes the incoming messages.
"""

import os
import sys
import json
import signal
import logging
from datetime import datetime
from typing import Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('truck-consumer')

# Configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '172.30.68.114:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'truck-telemetry')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP', 'truck-consumer-group')
KAFKA_CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'truck-consumer')
KAFKA_AUTO_OFFSET_RESET = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')

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


def create_kafka_consumer() -> Optional[KafkaConsumer]:
    """Create and configure the Kafka consumer."""
    try:
        config = {
            'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS.split(','),
            'client_id': KAFKA_CLIENT_ID,
            'group_id': KAFKA_CONSUMER_GROUP,
            'auto_offset_reset': KAFKA_AUTO_OFFSET_RESET,
            'enable_auto_commit': True,
            'auto_commit_interval_ms': 5000,
            'value_deserializer': lambda v: json.loads(v.decode('utf-8')),
            'key_deserializer': lambda k: k.decode('utf-8') if k else None,
        }

        # Add security configuration if specified
        if KAFKA_SECURITY_PROTOCOL != 'PLAINTEXT':
            config['security_protocol'] = KAFKA_SECURITY_PROTOCOL

        if KAFKA_SASL_MECHANISM:
            config['sasl_mechanism'] = KAFKA_SASL_MECHANISM
            config['sasl_plain_username'] = KAFKA_SASL_USERNAME
            config['sasl_plain_password'] = KAFKA_SASL_PASSWORD

        consumer = KafkaConsumer(KAFKA_TOPIC, **config)
        logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        logger.info(f"Subscribed to topic: {KAFKA_TOPIC}")
        return consumer

    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return None


def process_message(message) -> None:
    """Process a received Kafka message."""
    try:
        truck_id = message.key or 'unknown'
        payload = message.value
        
        # Extract truck data
        source = payload.get('source', 'unknown')
        polled_at = payload.get('polled_at', 'unknown')
        truck_data = payload.get('data', {})
        
        # Extract key truck information
        identification = truck_data.get('identification', {})
        location = truck_data.get('location', {})
        engine = truck_data.get('engine', {})
        payload_info = truck_data.get('payload', {})
        
        logger.info("=" * 60)
        logger.info(f"RECEIVED TRUCK TELEMETRY")
        logger.info("=" * 60)
        logger.info(f"Kafka Partition: {message.partition}, Offset: {message.offset}")
        logger.info(f"Truck ID: {truck_id}")
        logger.info(f"Asset Number: {identification.get('asset_number', 'N/A')}")
        logger.info(f"Model: {identification.get('model', 'N/A')}")
        logger.info(f"Polled At: {polled_at}")
        logger.info("-" * 40)
        logger.info(f"Location: {location.get('latitude', 0):.4f}, {location.get('longitude', 0):.4f}")
        logger.info(f"Speed: {location.get('speed', 0)} km/h")
        logger.info(f"Heading: {location.get('heading', 0)}°")
        logger.info("-" * 40)
        logger.info(f"Engine RPM: {engine.get('engine_rpm', 0)}")
        logger.info(f"Engine Temp: {engine.get('engine_temp', 0)}°C")
        logger.info(f"Fuel Level: {engine.get('fuel_level', 0)}%")
        logger.info("-" * 40)
        logger.info(f"Payload: {payload_info.get('payload_weight', 0)} tonnes")
        logger.info(f"Load Status: {payload_info.get('load_status', 'N/A')}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        logger.error(f"Raw message: {message.value}")


def main():
    """Main consumer loop."""
    global running

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 60)
    logger.info("BHP Proximity Truck Consumer Starting")
    logger.info("=" * 60)
    logger.info(f"Kafka Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC}")
    logger.info(f"Consumer Group: {KAFKA_CONSUMER_GROUP}")
    logger.info(f"Auto Offset Reset: {KAFKA_AUTO_OFFSET_RESET}")
    logger.info("=" * 60)

    # Create Kafka consumer
    consumer = create_kafka_consumer()
    if not consumer:
        logger.error("Could not create Kafka consumer, exiting")
        sys.exit(1)

    message_count = 0

    try:
        logger.info("Waiting for messages...")
        
        while running:
            # Poll for messages with a timeout
            messages = consumer.poll(timeout_ms=1000)
            
            for topic_partition, records in messages.items():
                for message in records:
                    message_count += 1
                    logger.info(f"Message #{message_count} received")
                    process_message(message)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

    finally:
        # Cleanup
        if consumer:
            logger.info("Closing Kafka consumer...")
            consumer.close()
            logger.info("Kafka consumer closed")

        logger.info(f"Total messages processed: {message_count}")
        logger.info("Truck Consumer shutdown complete")


if __name__ == "__main__":
    main()

