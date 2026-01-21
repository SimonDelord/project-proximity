# BHP Project Proximity

A proximity detection and collision avoidance system for mining fleet operations.

## Overview

This project implements real-time proximity monitoring for mining vehicles to enhance safety and prevent collisions in mining operations. It consists of three containerized microservices that work together to simulate truck telemetry, stream data to Kafka, and consume the data for processing.

## Architecture

```
┌─────────────────┐      HTTP       ┌─────────────────┐      Kafka      ┌─────────────────┐
│                 │    /trucks/     │                 │   truck-       │                 │
│   Truck API     │◄───────────────│  Truck Poller   │───telemetry───►│ Truck Consumer  │
│   (Port 80)     │    sample      │                 │    topic       │                 │
└─────────────────┘                └─────────────────┘                └─────────────────┘
```

## Components

### 1. Truck API (`src/api/`)

A FastAPI-based HTTP service that simulates a mining haul truck and exposes all its configuration parameters via REST endpoints.

**Features:**
- Exposes comprehensive truck telemetry data (94 parameters)
- Supports multiple truck models (Caterpillar, Komatsu, Liebherr, Hitachi)
- Provides truck identification, GPS location, engine metrics, payload data, safety status, and more

**Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `/` | API information and available endpoints |
| `/health` | Health check |
| `/trucks/schema` | Complete truck data model schema |
| `/trucks/models` | Available truck models |
| `/trucks/enums` | All enum types and values |
| `/trucks/parameters` | Flat list of all 94 truck parameters |
| `/trucks/sample` | Sample truck with realistic telemetry data |

**Build & Run:**
```bash
# Build from project root
docker build -t truck-api .

# Run
docker run -p 80:80 truck-api
```

**Test:**
```bash
curl http://localhost/trucks/sample
```

---

### 2. Truck Poller (`src/truck-poller/`)

A Python service that polls the Truck API at regular intervals and publishes the truck telemetry data as JSON payloads to a Kafka topic.

**Features:**
- Configurable polling interval
- Publishes full truck JSON payload to Kafka
- Uses truck_id as message key for proper partitioning
- Supports SASL authentication for secured Kafka clusters
- Graceful shutdown handling

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `TRUCK_API_URL` | `https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample` | URL of the Truck API |
| `KAFKA_BOOTSTRAP_SERVERS` | `172.30.68.114:9092` | Kafka broker addresses |
| `KAFKA_TOPIC` | `truck-telemetry` | Target Kafka topic |
| `POLL_INTERVAL_SECONDS` | `10` | Polling frequency in seconds |
| `KAFKA_CLIENT_ID` | `truck-poller` | Kafka client identifier |
| `KAFKA_SECURITY_PROTOCOL` | `PLAINTEXT` | Security protocol |

**Kafka Message Format:**
```json
{
  "source": "truck-poller",
  "polled_at": "2026-01-22T10:30:00.000000",
  "api_url": "https://...",
  "data": {
    "identification": { "truck_id": "TRK-001", ... },
    "location": { "latitude": -23.3617, "longitude": 118.7083, ... },
    "engine": { "engine_rpm": 1800, ... },
    ...
  }
}
```

**Build & Run:**
```bash
cd src/truck-poller
docker build -t truck-poller .

docker run \
  -e TRUCK_API_URL=http://truck-api/trucks/sample \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e POLL_INTERVAL_SECONDS=5 \
  truck-poller
```

---

### 3. Truck Consumer (`src/truck-consumer/`)

A Python service that consumes truck telemetry messages from the Kafka topic and logs/displays the data.

**Features:**
- Subscribes to the truck-telemetry Kafka topic
- Deserializes and displays truck data in a formatted log output
- Consumer group support for scalability
- Configurable auto offset reset (earliest/latest)
- Graceful shutdown handling

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `172.30.68.114:9092` | Kafka broker addresses |
| `KAFKA_TOPIC` | `truck-telemetry` | Kafka topic to consume |
| `KAFKA_CONSUMER_GROUP` | `truck-consumer-group` | Consumer group ID |
| `KAFKA_CLIENT_ID` | `truck-consumer` | Kafka client identifier |
| `KAFKA_AUTO_OFFSET_RESET` | `earliest` | Where to start consuming |
| `KAFKA_SECURITY_PROTOCOL` | `PLAINTEXT` | Security protocol |

**Build & Run:**
```bash
cd src/truck-consumer
docker build -t truck-consumer .

docker run \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e KAFKA_TOPIC=truck-telemetry \
  truck-consumer
```

---

## Project Structure

```
BHP-project-proximity/
├── configs/
│   └── openshift/                    # OpenShift deployment manifests
│       ├── truck-poller-deployment.yaml
│       ├── truck-poller-configmap.yaml
│       └── truck-consumer-deployment.yaml
├── src/
│   ├── api/                          # Truck API service
│   │   ├── app.py                    # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── models/                       # Data models
│   │   ├── truck.py                  # Truck dataclasses and enums
│   │   ├── truck_schema.json         # JSON schema
│   │   └── schema.sql                # SQL schema
│   ├── truck-poller/                 # Kafka producer service
│   │   ├── poller.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── truck-consumer/               # Kafka consumer service
│       ├── consumer.py
│       ├── requirements.txt
│       └── Dockerfile
├── scripts/                          # Utility scripts
├── data/                             # Sample data files
├── docs/                             # Documentation
├── tests/                            # Test files
├── monitoring/                       # Monitoring configs
├── Dockerfile                        # Truck API Dockerfile (root)
└── README.md
```

## Deployment on OpenShift

### Deploy Truck API
```bash
oc new-app --name=truck-api --binary --strategy=docker
oc start-build truck-api --from-dir=. --follow
```

### Deploy Truck Poller
```bash
oc new-build --name=truck-poller --binary --strategy=docker
oc start-build truck-poller --from-dir=src/truck-poller --follow
oc apply -f configs/openshift/truck-poller-deployment.yaml
oc set image deployment/truck-poller truck-poller=image-registry.openshift-image-registry.svc:5000/$(oc project -q)/truck-poller:latest
```

### Deploy Truck Consumer
```bash
oc new-build --name=truck-consumer --binary --strategy=docker
oc start-build truck-consumer --from-dir=src/truck-consumer --follow
oc apply -f configs/openshift/truck-consumer-deployment.yaml
oc set image deployment/truck-consumer truck-consumer=image-registry.openshift-image-registry.svc:5000/$(oc project -q)/truck-consumer:latest
```

### Verify Deployments
```bash
oc get pods
oc logs -f deployment/truck-poller
oc logs -f deployment/truck-consumer
```

## Truck Data Model

The truck model includes 94 parameters across 13 categories:

| Category | Parameters | Description |
|----------|------------|-------------|
| Identification | 9 | Truck ID, asset number, model, fleet, site |
| Location | 7 | GPS coordinates, speed, heading, altitude |
| Engine | 11 | RPM, temperatures, fuel level, oil pressure |
| Payload | 6 | Weight, load status, tray position, cycle count |
| Brakes | 8 | Temperatures, wear, retarder, parking brake |
| Hydraulics | 4 | Pressure, temperature, fluid level |
| Electrical | 5 | Battery voltage, alternator, power status |
| Safety | 9 | Seatbelt, operator, fatigue, emergency stop |
| Proximity | 9 | Nearest vehicle, collision warnings, zones |
| Zone | 6 | Current zone, speed limit, authorization |
| Operations | 8 | Odometer, operating mode, shift, idle time |
| Maintenance | 7 | Service dates, fault codes, warning lights |
| Tyres | 5 | Pressure, temperature, wear (×6 tyres) |

## License

Proprietary - BHP Internal Use Only
