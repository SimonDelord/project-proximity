# BHP Project Proximity

A proximity detection and collision avoidance system for mining fleet operations.

## Overview

This project implements real-time proximity monitoring for mining vehicles to enhance safety and prevent collisions in mining operations. It consists of multiple containerized microservices that work together to simulate truck telemetry, stream data to Kafka, process/filter events, and consume data for downstream processing.

## Architecture

```
                                        ┌─────────────────────────────────────────────────────────────┐
                                        │                        KAFKA                                │
                                        │  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐  │
                                        │  │ truck-telemetry │  │truck-telemetry-  │  │ eda-topic │  │
                                        │  │                 │  │     camel        │  │           │  │
                                        │  └────────▲────────┘  └────────▲─────────┘  └─────▲─────┘  │
                                        │           │                    │                  │        │
                                        └───────────┼────────────────────┼──────────────────┼────────┘
                                                    │                    │                  │
┌─────────────────┐      HTTP       ┌───────────────┴───┐    ┌──────────┴─────────┐    ┌──┴────────────────┐
│                 │    /trucks/     │                   │    │                    │    │                   │
│   Truck API     │◄───────────────│   Truck Poller    │    │  Truck Poller      │    │  Truck EDA Filter │
│   (FastAPI)     │    sample      │   (Python)        │    │  (Camel/Quarkus)   │    │  (Camel/Quarkus)  │
│                 │                │                   │    │                    │    │                   │
└─────────────────┘                └───────────────────┘    └────────────────────┘    └───────────────────┘
        │                                                            │                         │
        │                                                            │                         │
        └────────────────────────────────────────────────────────────┘                         │
                                    HTTP polling                                               │
                                                                                               │
                                                    ┌──────────────────────────────────────────┘
                                                    │  Consumes from truck-telemetry-camel
                                                    │  Filters: truck_id + firmware_version
                                                    │  Publishes to: eda-topic
                                                    ▼
┌─────────────────┐                     ┌───────────────────────────────────────────────────────────────┐
│                 │                     │                        EDA Message                            │
│ Truck Consumer  │◄────────────────────│  {"event_type": "truck_telemetry_filtered",                  │
│ (Python)        │   truck-telemetry   │   "truck_id": "TRK-001", "firmware_version": "2.4.1"}        │
│                 │                     └───────────────────────────────────────────────────────────────┘
└─────────────────┘
```

## Components

### 1. Truck API (`src/api/`)

A **FastAPI**-based HTTP service that simulates a mining haul truck and exposes all its configuration parameters via REST endpoints.

| Feature | Description |
|---------|-------------|
| Framework | Python / FastAPI |
| Port | 80 |
| Parameters | 94 telemetry parameters |
| Truck Models | Caterpillar, Komatsu, Liebherr, Hitachi |

**Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `/` | API information |
| `/health` | Health check |
| `/trucks/schema` | Complete data model schema |
| `/trucks/models` | Available truck models |
| `/trucks/parameters` | All 94 parameters |
| `/trucks/sample` | Sample truck telemetry |

---

### 2. Truck Poller - Python (`src/truck-poller/`)

A **Python** service that polls the Truck API and publishes telemetry to Kafka.

| Feature | Description |
|---------|-------------|
| Framework | Python / kafka-python |
| Publishes to | `truck-telemetry` topic |
| Poll Interval | Configurable (default 10s) |

---

### 3. Truck Poller - Camel (`src/truck-poller-camel/`)

A **Camel Quarkus** service that polls the Truck API and publishes telemetry to Kafka.

| Feature | Description |
|---------|-------------|
| Framework | Apache Camel / Quarkus |
| Publishes to | `truck-telemetry-camel` topic |
| Poll Interval | Configurable (default 10s) |

**Camel Route:**
```
Timer (10s) → HTTP GET (Truck API) → Transform → Kafka (truck-telemetry-camel)
```

---

### 4. Truck EDA Filter (`src/truck-eda-filter/`)

A **Camel Quarkus** service that consumes truck telemetry, filters to extract key fields, and publishes to an EDA (Event-Driven Architecture) topic.

| Feature | Description |
|---------|-------------|
| Framework | Apache Camel / Quarkus |
| Consumes from | `truck-telemetry-camel` topic |
| Publishes to | `eda-topic` |
| Filters | `truck_id`, `firmware_version` |

**Camel Route:**
```
Kafka (truck-telemetry-camel) → Filter/Transform → Kafka (eda-topic)
```

**EDA Message Format:**
```json
{
  "event_type": "truck_telemetry_filtered",
  "timestamp": "2026-01-29T07:46:44.139Z",
  "source_topic": "truck-telemetry-camel",
  "truck_id": "TRK-001",
  "firmware_version": "2.4.1-build.2847"
}
```

---

### 5. Truck Consumer (`src/truck-consumer/`)

A **Python** service that consumes truck telemetry from Kafka and displays/logs the data.

| Feature | Description |
|---------|-------------|
| Framework | Python / kafka-python |
| Consumes from | `truck-telemetry` topic |
| Consumer Group | `truck-consumer-group` |

---

## Project Structure

```
BHP-project-proximity/
├── configs/
│   └── openshift/                          # OpenShift deployment manifests
│       ├── kafka/                          # Kafka configuration
│       │   ├── kafka-cluster.yaml          # Kafka cluster CR (Strimzi)
│       │   ├── kafka-topics.yaml           # Topic definitions
│       │   └── kafka-console.yaml          # AMQ Streams Console
│       ├── truck-poller-deployment.yaml    # Python poller deployment
│       ├── truck-poller-camel-deployment.yaml  # Camel poller deployment
│       ├── truck-consumer-deployment.yaml  # Python consumer deployment
│       └── truck-eda-filter-deployment.yaml    # Camel EDA filter deployment
│
├── src/
│   ├── api/                                # Truck API (FastAPI)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── models/                             # Data models
│   │   ├── truck.py                        # Truck dataclasses (94 params)
│   │   ├── truck_schema.json               # JSON schema
│   │   └── schema.sql                      # SQL schema
│   │
│   ├── truck-poller/                       # Python Kafka producer
│   │   ├── poller.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── truck-poller-camel/                 # Camel Kafka producer
│   │   ├── pom.xml
│   │   ├── Dockerfile
│   │   └── src/main/java/.../TruckPollerRoute.java
│   │
│   ├── truck-eda-filter/                   # Camel EDA filter
│   │   ├── pom.xml
│   │   ├── Dockerfile
│   │   └── src/main/java/.../TruckEdaFilterRoute.java
│   │
│   └── truck-consumer/                     # Python Kafka consumer
│       ├── consumer.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── scripts/                                # Utility scripts
├── data/                                   # Sample data files
├── docs/                                   # Documentation
├── tests/                                  # Test files
├── monitoring/                             # Monitoring configs
├── Dockerfile                              # Truck API Dockerfile (root)
└── README.md
```

## Kafka Topics

| Topic | Description | Producers | Consumers |
|-------|-------------|-----------|-----------|
| `truck-telemetry` | Full truck telemetry (Python poller) | truck-poller | truck-consumer |
| `truck-telemetry-camel` | Full truck telemetry (Camel poller) | truck-poller-camel | truck-eda-filter |
| `eda-topic` | Filtered events (truck_id + firmware) | truck-eda-filter | External systems |

## Deployment on OpenShift

### Prerequisites
- OpenShift cluster with AMQ Streams operator installed
- AMQ Streams Console operator (optional)

### 1. Deploy Kafka Cluster
```bash
oc new-project kafka-demo
oc apply -f configs/openshift/kafka/kafka-cluster.yaml
oc wait kafka/my-cluster --for=condition=Ready --timeout=300s
oc apply -f configs/openshift/kafka/kafka-topics.yaml
```

### 2. Deploy Truck API
```bash
oc project trucks  # or your target namespace
oc new-app --name=project-proximity-git https://github.com/SimonDelord/project-proximity.git
```

### 3. Deploy Python Poller
```bash
oc new-build --name=truck-poller --binary --strategy=docker
oc start-build truck-poller --from-dir=src/truck-poller --follow
oc apply -f configs/openshift/truck-poller-deployment.yaml
```

### 4. Deploy Camel Poller
```bash
oc new-build --name=truck-poller-camel --binary --strategy=docker
oc start-build truck-poller-camel --from-dir=src/truck-poller-camel --follow
oc apply -f configs/openshift/truck-poller-camel-deployment.yaml
```

### 5. Deploy EDA Filter
```bash
oc new-build --name=truck-eda-filter --binary --strategy=docker
oc start-build truck-eda-filter --from-dir=src/truck-eda-filter --follow
oc apply -f configs/openshift/truck-eda-filter-deployment.yaml
```

### 6. Deploy Consumer
```bash
oc new-build --name=truck-consumer --binary --strategy=docker
oc start-build truck-consumer --from-dir=src/truck-consumer --follow
oc apply -f configs/openshift/truck-consumer-deployment.yaml
```

### 7. Deploy AMQ Streams Console (Optional)
```bash
oc apply -f configs/openshift/kafka/kafka-console.yaml
```

### Verify Deployments
```bash
oc get pods
oc logs -f deployment/truck-poller-camel
oc logs -f deployment/truck-eda-filter
```

## Truck Data Model

The truck model includes **94 parameters** across 13 categories:

| Category | # Params | Examples |
|----------|----------|----------|
| Identification | 9 | truck_id, asset_number, model, firmware_version |
| Location | 7 | latitude, longitude, speed, heading |
| Engine | 11 | engine_rpm, engine_temp, fuel_level |
| Payload | 6 | payload_weight, load_status, cycle_count |
| Brakes | 8 | brake_temp, retarder_active, parking_brake |
| Hydraulics | 4 | hydraulic_pressure, hydraulic_temp |
| Electrical | 5 | battery_voltage, alternator_output |
| Safety | 9 | seatbelt_fastened, operator_id, fatigue_score |
| Proximity | 9 | nearest_vehicle_distance, collision_warning |
| Zone | 6 | current_zone_id, speed_limit |
| Operations | 8 | odometer, operating_mode, shift_id |
| Maintenance | 7 | last_service_date, active_fault_codes |
| Tyres | 5 | pressure, temperature, wear (×6 tyres) |

## Environment Variables

### Truck Poller (Python & Camel)
| Variable | Default | Description |
|----------|---------|-------------|
| `TRUCK_API_URL` | `https://...` | Truck API endpoint |
| `KAFKA_BOOTSTRAP_SERVERS` | `172.30.68.114:9092` | Kafka brokers |
| `KAFKA_TOPIC` | `truck-telemetry` | Target topic |
| `POLL_INTERVAL_SECONDS` | `10` | Polling frequency |

### EDA Filter (Camel)
| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BROKERS` | `172.30.68.114:9092` | Kafka brokers |
| `KAFKA_SOURCE_TOPIC` | `truck-telemetry-camel` | Source topic |
| `KAFKA_TARGET_TOPIC` | `eda-topic` | Target topic |
| `KAFKA_CONSUMER_GROUP` | `truck-eda-filter-group` | Consumer group |

## License

Proprietary - BHP Internal Use Only
