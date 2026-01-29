# BHP Project Proximity

A proximity detection and collision avoidance system for mining fleet operations.

## Overview

This project implements real-time proximity monitoring for mining vehicles to enhance safety and prevent collisions in mining operations. It consists of multiple containerized microservices that work together to simulate truck telemetry, stream data to Kafka, process/filter events, and consume data for downstream processing.

## Architecture

```
┌────────────────────────────────────┐
│        10 SAMPLE TRUCKS            │
│  ┌──────┐ ┌──────┐     ┌──────┐   │
│  │TRK-01│ │TRK-02│ ... │TRK-10│   │
│  │v2.4.1│ │v2.4.1│     │v3.1.2│   │
│  └──┬───┘ └──┬───┘     └──┬───┘   │
│     └────────┴───────────┴────────┤
└───────────────┬───────────────────┘
                │
                │  HTTP /trucks/sample
                │  (polls every 5 seconds)
                ▼
┌───────────────────────────────────┐
│     Truck Poller (Camel/Quarkus)  │
│     polls 10 trucks               │
└───────────────┬───────────────────┘
                │
                │  publishes
                ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                    KAFKA                                          │
│                                                                                   │
│   ┌──────────────────────┐                              ┌───────────────────┐    │
│   │ truck-telemetry-camel│                              │     eda-topic     │    │
│   │                      │                              │                   │    │
│   └──────────┬───────────┘                              └─────────▲─────────┘    │
│              │                                                    │              │
└──────────────┼────────────────────────────────────────────────────┼──────────────┘
               │                                                    │
               │  consumes                                          │  publishes
               ▼                                                    │
┌───────────────────────────────────┐                               │
│   Truck EDA Filter (Camel/Quarkus)│───────────────────────────────┘
│                                   │
│   Filters:                        │
│   - truck_id                      │
│   - firmware_version              │
└───────────────────────────────────┘
                │
                │  EDA Message Output:
                ▼
┌───────────────────────────────────────────────────────────────┐
│  {                                                            │
│    "event_type": "truck_telemetry_filtered",                  │
│    "truck_id": "TRK-001",                                     │
│    "firmware_version": "2.4.1-build.2847"                     │
│  }                                                            │
└───────────────────────────────────────────────────────────────┘
```

## Components

### 1. Sample Trucks Fleet (`src/sample_trucks/` + `configs/sample-trucks/`)

A fleet of **10 configurable truck API instances**, each with unique configurations simulating different trucks in the mine.

| Truck | ID | Firmware | Zone | Model |
|-------|-----|----------|------|-------|
| truck-01 | TRK-001 | 2.4.1-build.2847 | Main Pit North | CAT 797F |
| truck-02 | TRK-002 | 2.4.1-build.2850 | Main Pit North | CAT 797F |
| truck-03 | TRK-003 | 2.4.1-build.2853 | Main Pit South | Komatsu 930E |
| truck-04 | TRK-004 | 2.4.1-build.2860 | Main Pit South | Komatsu 930E |
| truck-05 | TRK-005 | 3.0.0-build.3001 | North Haul Road | Liebherr T284 |
| truck-06 | TRK-006 | 3.0.0-build.3005 | North Haul Road | Liebherr T284 |
| truck-07 | TRK-007 | 3.0.0-build.3010 | Waste Dump Alpha | CAT 797F |
| truck-08 | TRK-008 | 3.1.2-build.3120 | Waste Dump Alpha | Hitachi EH5000 |
| truck-09 | TRK-009 | 3.1.2-build.3125 | Loading Bay East | Komatsu 980E |
| truck-10 | TRK-010 | 3.1.2-build.3130 | Loading Bay East | CAT 793F |

**3 Firmware Versions:**
- **v2.4.1** - Trucks 1-4 (Legacy)
- **v3.0.0** - Trucks 5-7 (Current stable)
- **v3.1.2** - Trucks 8-10 (Latest release)

---

### 2. Truck API (`src/api/`)

A **FastAPI**-based HTTP service that simulates a mining haul truck and exposes all its configuration parameters via REST endpoints.

| Feature | Description |
|---------|-------------|
| Framework | Python / FastAPI |
| Port | 8080 |
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

### 3. Truck Poller - Camel (`src/truck-poller-camel/`)

A **Camel Quarkus** service that polls **multiple Truck APIs** (10 trucks) and publishes telemetry to Kafka.

| Feature | Description |
|---------|-------------|
| Framework | Apache Camel / Quarkus |
| Publishes to | `truck-telemetry-camel` topic |
| Poll Interval | 5 seconds (configurable) |
| Trucks Polled | 10 concurrent endpoints |

**Camel Route:**
```
Timer (5s) → HTTP GET (10 Truck APIs) → Transform → Kafka (truck-telemetry-camel)
```

---

### 4. Truck EDA Filter (`src/truck-eda-filter/`)

A **Camel Quarkus** service that consumes truck telemetry from `truck-telemetry-camel`, filters to extract key fields, and publishes to `eda-topic`.

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

## Project Structure

```
BHP-project-proximity/
├── configs/
│   ├── openshift/                          # OpenShift deployment manifests
│   │   ├── kafka/                          # Kafka configuration
│   │   │   ├── kafka-cluster.yaml          # Kafka cluster CR (Strimzi)
│   │   │   ├── kafka-topics.yaml           # Topic definitions
│   │   │   └── kafka-console.yaml          # AMQ Streams Console
│   │   ├── truck-poller-camel-deployment.yaml  # Camel poller deployment
│   │   └── truck-eda-filter-deployment.yaml    # Camel EDA filter deployment
│   │
│   └── sample-trucks/                      # 10 Sample Truck deployments
│       ├── README.md                       # Sample trucks documentation
│       ├── all-trucks.yaml                 # Combined manifest for all 10
│       ├── truck-01-deployment.yaml        # Individual truck manifests
│       ├── truck-02-deployment.yaml
│       └── ... (truck-03 through truck-10)
│
├── src/                                    # Source code (see src/README.md)
│   ├── README.md                           # Source code documentation
│   ├── api/                                # Truck API (FastAPI)
│   ├── models/                             # Data models
│   ├── sample_trucks/                      # Configurable sample truck API
│   ├── truck-poller-camel/                 # Camel Kafka producer (multi-truck)
│   └── truck-eda-filter/                   # Camel EDA filter
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

### 2. Deploy 10 Sample Trucks
```bash
oc new-project trucks

# Create build config
oc new-build --name=sample-truck --binary --strategy=docker

# Build the image (from project root)
oc start-build sample-truck --from-dir=. --follow

# Deploy all 10 trucks
oc apply -f configs/sample-trucks/all-trucks.yaml

# Verify
oc get pods
oc get routes
```

### 3. Deploy Camel Poller (Multi-Truck)
```bash
oc project kafka-demo
oc new-build --name=truck-poller-camel --binary --strategy=docker
oc start-build truck-poller-camel --from-dir=src/truck-poller-camel --follow
oc apply -f configs/openshift/truck-poller-camel-deployment.yaml
```

### 4. Deploy EDA Filter
```bash
oc new-build --name=truck-eda-filter --binary --strategy=docker
oc start-build truck-eda-filter --from-dir=src/truck-eda-filter --follow
oc apply -f configs/openshift/truck-eda-filter-deployment.yaml
```

### 5. Deploy AMQ Streams Console (Optional)
```bash
oc apply -f configs/openshift/kafka/kafka-console.yaml
```

### Verify Deployments
```bash
# Check all pods
oc get pods -n trucks
oc get pods -n kafka-demo

# View Camel poller logs (should see 10 trucks being polled)
oc logs -f deployment/truck-poller-camel -n kafka-demo

# View EDA filter logs
oc logs -f deployment/truck-eda-filter -n kafka-demo
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

### Truck Poller (Camel)
| Variable | Default | Description |
|----------|---------|-------------|
| `TRUCK_API_URLS` | `https://truck-XX-trucks...` | Comma-separated truck endpoints |
| `KAFKA_BROKERS` | `172.30.68.114:9092` | Kafka brokers |
| `KAFKA_TOPIC` | `truck-telemetry-camel` | Target topic |
| `POLL_INTERVAL_SECONDS` | `5` | Polling frequency |

### Sample Trucks
| Variable | Default | Description |
|----------|---------|-------------|
| `TRUCK_ID` | `TRK-001` | Unique truck identifier |
| `TRUCK_NUMBER` | `1` | Numeric truck number (1-10) |
| `FIRMWARE_VERSION` | `2.4.1-build.2847` | Firmware version |
| `FLEET_ID` | `BHP-WA-001` | Fleet identifier |

### EDA Filter (Camel)
| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BROKERS` | `172.30.68.114:9092` | Kafka brokers |
| `KAFKA_SOURCE_TOPIC` | `truck-telemetry-camel` | Source topic |
| `KAFKA_TARGET_TOPIC` | `eda-topic` | Target topic |
| `KAFKA_CONSUMER_GROUP` | `truck-eda-filter-group` | Consumer group |

## License

Proprietary - BHP Internal Use Only
