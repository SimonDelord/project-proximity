# Project Proximity - Source Code

This directory contains all the source code for the Project Proximity microservices.

## Directory Structure

```
src/
├── api/                    # Original Truck API (FastAPI)
├── models/                 # Shared data models
├── sample_trucks/          # Configurable multi-truck API
├── truck-poller/           # Python Kafka producer
├── truck-poller-camel/     # Camel Kafka producer (multi-truck)
├── truck-eda-filter/       # Camel EDA filter service
├── truck-eda-filter-aap/   # Camel EDA filter for AAP (multi-format)
└── truck-consumer/         # Python Kafka consumer
```

---

## Components Overview

### 1. `api/` - Truck API (FastAPI)

The original truck API that exposes a single truck's telemetry data.

| File | Description |
|------|-------------|
| `app.py` | FastAPI application with endpoints |
| `requirements.txt` | Python dependencies |

**Run locally:**
```bash
cd api
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

---

### 2. `models/` - Data Models

Shared data models used across multiple services.

| File | Description |
|------|-------------|
| `truck.py` | Python dataclasses defining 94 truck parameters |
| `truck_schema.json` | JSON schema for validation |
| `schema.sql` | SQL schema for database storage |

**Truck Categories:**
- Identification (truck_id, model, firmware_version)
- Location (GPS, speed, heading)
- Engine (RPM, temp, fuel level)
- Payload (weight, load status)
- Brakes, Hydraulics, Electrical
- Safety (operator, seatbelt, lights)
- Proximity (nearest vehicle, collision warning)
- Zone (current zone, speed limit)
- Operations (odometer, shift)
- Maintenance (service hours, faults)
- Tyres (pressure, temperature × 6)

---

### 3. `sample_trucks/` - Configurable Sample Truck API

A configurable version of the Truck API that generates unique data based on environment variables. Used to deploy 10 different truck instances.

| File | Description |
|------|-------------|
| `app.py` | FastAPI app with configurable truck data |
| `Dockerfile` | Container image definition |
| `requirements.txt` | Python dependencies |

**Environment Variables:**
| Variable | Example | Description |
|----------|---------|-------------|
| `TRUCK_ID` | `TRK-001` | Unique truck identifier |
| `TRUCK_NUMBER` | `1` | Numeric ID (1-10) for data variation |
| `FIRMWARE_VERSION` | `2.4.1-build.2847` | Firmware version |
| `FLEET_ID` | `FLEET-WA-001` | Fleet identifier |

**Build and Deploy:**
```bash
# From project root
oc new-build --name=sample-truck --binary --strategy=docker -n trucks
oc start-build sample-truck --from-dir=. --follow -n trucks

# Deploy (see configs/sample-trucks/)
oc apply -f configs/sample-trucks/all-trucks.yaml
```

---

### 4. `truck-poller/` - Python Kafka Producer

Polls a single truck API and publishes to Kafka using Python's kafka-python library.

| File | Description |
|------|-------------|
| `poller.py` | Main polling logic |
| `Dockerfile` | Container image definition |
| `requirements.txt` | Python dependencies (requests, kafka-python) |

**Build and Deploy:**
```bash
oc new-build --name=truck-poller --binary --strategy=docker
oc start-build truck-poller --from-dir=src/truck-poller --follow
oc apply -f configs/openshift/truck-poller-deployment.yaml
```

---

### 5. `truck-poller-camel/` - Camel Kafka Producer (Multi-Truck)

A Camel Quarkus application that polls **multiple truck APIs** simultaneously and publishes to Kafka.

| File | Description |
|------|-------------|
| `pom.xml` | Maven project file with Camel Quarkus dependencies |
| `Dockerfile` | Multi-stage build (Maven + JRE) |
| `src/main/java/.../TruckPollerRoute.java` | Camel route definition |
| `src/main/resources/application.properties` | Configuration |

**Key Features:**
- Polls 10 truck endpoints every 5 seconds
- Staggered requests (500ms offset per truck)
- Automatic retry on failure
- Enriches messages with metadata

**Camel Route Logic:**
```java
// For each truck URL in the comma-separated list:
from("timer:truckPollerN?period=5000&delay=N*500")
    .to("https://truck-XX-trucks.../trucks/sample")
    .process(exchange -> { /* Add metadata */ })
    .to("kafka:truck-telemetry-camel?brokers=...");
```

#### Building truck-poller-camel

**Prerequisites:**
- Java 17+
- Maven 3.9+
- Docker (for container build)

**Local Build (without container):**
```bash
cd src/truck-poller-camel

# Build with Maven
mvn clean package -DskipTests

# Run locally (with custom truck URLs)
java -Dtruck.api.urls="http://localhost:8081/trucks/sample,http://localhost:8082/trucks/sample" \
     -Dkafka.brokers="localhost:9092" \
     -jar target/quarkus-app/quarkus-run.jar
```

**Container Build on OpenShift:**
```bash
# Navigate to project root
cd /path/to/project-proximity

# Switch to the kafka-demo namespace
oc project kafka-demo

# Create a build config (first time only)
oc new-build --name=truck-poller-camel --binary --strategy=docker

# Start the build from the truck-poller-camel directory
oc start-build truck-poller-camel --from-dir=src/truck-poller-camel --follow

# The build will:
# 1. Upload src/truck-poller-camel/ to OpenShift
# 2. Run Maven build inside the container
# 3. Create a JRE-based runtime image
# 4. Push to the internal registry
```

#### Configuring the 10 Truck API URLs

The truck API URLs are passed to the container via the **`TRUCK_API_URLS`** environment variable in the deployment manifest. This is a **comma-separated list** of all truck endpoints.

**Method 1: Via Deployment YAML (Recommended)**

The deployment manifest (`configs/openshift/truck-poller-camel-deployment.yaml`) contains the environment variable:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truck-poller-camel
spec:
  template:
    spec:
      containers:
        - name: truck-poller-camel
          image: image-registry.openshift-image-registry.svc:5000/kafka-demo/truck-poller-camel:latest
          env:
            # Comma-separated list of 10 truck API endpoints
            - name: TRUCK_API_URLS
              value: "https://truck-01-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-02-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-03-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-04-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-05-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-06-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-07-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-08-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-09-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,https://truck-10-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample"
            - name: KAFKA_TOPIC
              value: "truck-telemetry-camel"
            - name: KAFKA_BROKERS
              value: "172.30.68.114:9092"
            - name: POLL_INTERVAL_SECONDS
              value: "5"
```

**Deploy with the URLs configured:**
```bash
# Apply the deployment (URLs are in the YAML)
oc apply -f configs/openshift/truck-poller-camel-deployment.yaml

# Verify it's running
oc get pods -l app=truck-poller-camel
oc logs -f deployment/truck-poller-camel
```

**Method 2: Override URLs at Runtime with `oc set env`**

You can also update the URLs after deployment:

```bash
# Update the truck URLs (single command, comma-separated)
oc set env deployment/truck-poller-camel \
  TRUCK_API_URLS="https://truck-01-trucks.apps.example.com/trucks/sample,https://truck-02-trucks.apps.example.com/trucks/sample,https://truck-03-trucks.apps.example.com/trucks/sample"

# This will automatically restart the pod with the new URLs
```

**Method 3: Default URLs in application.properties**

The `application.properties` file contains default URLs that are baked into the image:

```properties
# src/truck-poller-camel/src/main/resources/application.properties

# Default truck API URLs (can be overridden by TRUCK_API_URLS env var)
truck.api.urls=\
https://truck-01-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,\
https://truck-02-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,\
https://truck-03-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample,\
... (up to truck-10)
```

> **Note:** Environment variables set in the deployment YAML will **override** the values in `application.properties`.

#### URL Format

Each truck URL follows this pattern:
```
https://truck-{NN}-trucks.apps.{cluster-domain}/trucks/sample
```

Where:
- `{NN}` is the truck number (01, 02, ... 10)
- `{cluster-domain}` is your OpenShift cluster domain

**Example for 10 trucks:**
```
https://truck-01-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-02-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-03-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-04-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-05-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-06-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-07-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-08-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-09-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
https://truck-10-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
```

**Expected Log Output:**
```
08:46:26 INFO  [truck-poller-route-1] Polling Truck 1: https://truck-01-trucks.../trucks/sample
08:46:26 INFO  [truck-poller-route-1] Published Truck 1 to truck-telemetry-camel
08:46:26 INFO  [truck-poller-route-2] Polling Truck 2: https://truck-02-trucks.../trucks/sample
08:46:26 INFO  [truck-poller-route-2] Published Truck 2 to truck-telemetry-camel
08:46:26 INFO  [truck-poller-route-3] Polling Truck 3: https://truck-03-trucks.../trucks/sample
...
08:46:29 INFO  [truck-poller-route-10] Polling Truck 10: https://truck-10-trucks.../trucks/sample
08:46:29 INFO  [truck-poller-route-10] Published Truck 10 to truck-telemetry-camel
```

**Full Configuration Reference (`application.properties`):**
```properties
# Comma-separated list of truck API URLs
truck.api.urls=https://truck-01-trucks.../trucks/sample,https://truck-02-trucks.../trucks/sample,...

# Poll every 5 seconds
poll.interval.seconds=5

# Kafka configuration
kafka.topic=truck-telemetry-camel
kafka.brokers=172.30.68.114:9092
```

**Dockerfile Explained:**
```dockerfile
# Stage 1: Build with Maven
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B          # Cache dependencies
COPY src ./src
RUN mvn package -DskipTests -B            # Build the app

# Stage 2: Runtime with JRE
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/quarkus-app/ ./
CMD ["java", "-jar", "quarkus-run.jar"]
```

---

### 6. `truck-eda-filter/` - Camel EDA Filter

A Camel Quarkus application that consumes from Kafka, filters messages, and publishes to an EDA topic.

| File | Description |
|------|-------------|
| `pom.xml` | Maven project file |
| `Dockerfile` | Multi-stage build |
| `src/main/java/.../TruckEdaFilterRoute.java` | Camel route |
| `src/main/resources/application.properties` | Configuration |

**Build and Deploy:**
```bash
oc new-build --name=truck-eda-filter --binary --strategy=docker
oc start-build truck-eda-filter --from-dir=src/truck-eda-filter --follow
oc apply -f configs/openshift/truck-eda-filter-deployment.yaml
```

---

### 7. `truck-eda-filter-aap/` - Camel EDA Filter for AAP

A Camel Quarkus application similar to truck-eda-filter, but designed for **AAP (Ansible Automation Platform)** integration. It handles multiple payload formats commonly seen in AAP event sources.

| File | Description |
|------|-------------|
| `pom.xml` | Maven project file |
| `Dockerfile` | Multi-stage build |
| `src/main/java/.../TruckEdaFilterRoute.java` | Camel route with multi-format support |
| `src/main/resources/application.properties` | Configuration |

**Key Feature - Multi-Format Payload Support:**

The route handles three different JSON payload structures:

1. **Direct format:** `{ "identification": { "truck_id": "...", "firmware_version": "..." } }`
2. **Wrapped format:** `{ "key": "...", "value": { "identification": { ... } } }`
3. **Legacy format:** `{ "data": { "identification": { ... } } }`

**Configuration:**
| Property | Default | Description |
|----------|---------|-------------|
| `kafka.brokers` | `my-cluster-kafka-bootstrap:9092` | Kafka bootstrap servers |
| `kafka.source.topic` | `truck-telemetry-aap` | Source topic |
| `kafka.target.topic` | `truck-telemetry-aap-eda` | Target topic |
| `kafka.consumer.group` | `truck-eda-aap-filter-group` | Consumer group |

**Build and Deploy:**
```bash
oc new-build --name=truck-eda-aap-filter --binary --strategy=docker -n kafka-demo
oc start-build truck-eda-aap-filter --from-dir=src/truck-eda-filter-aap --follow -n kafka-demo
oc apply -f configs/openshift/truck-eda-aap-filter-deployment.yaml
```

**Output Message Format:**
```json
{
  "event_type": "truck_telemetry_filtered",
  "timestamp": "2026-02-19T23:36:56.491Z",
  "source_topic": "truck-telemetry-aap",
  "truck_id": "TRK-009",
  "firmware_version": "3.1.2-build.3125"
}
```

---

### 8. `truck-consumer/` - Python Kafka Consumer

A simple Python consumer that reads from Kafka and logs messages.

| File | Description |
|------|-------------|
| `consumer.py` | Kafka consumer logic |
| `Dockerfile` | Container image definition |
| `requirements.txt` | Python dependencies (kafka-python) |

**Build and Deploy:**
```bash
oc new-build --name=truck-consumer --binary --strategy=docker
oc start-build truck-consumer --from-dir=src/truck-consumer --follow
oc apply -f configs/openshift/truck-consumer-deployment.yaml
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **API** | Python 3.11, FastAPI, Uvicorn |
| **Camel Services** | Java 17, Quarkus, Apache Camel |
| **Message Broker** | Apache Kafka (AMQ Streams) |
| **Container Runtime** | OpenShift / Kubernetes |
| **Build** | Maven (Java), pip (Python) |

## Development Tips

### Running Camel Services Locally

1. **Install Java 17:**
   ```bash
   # macOS
   brew install openjdk@17
   
   # Set JAVA_HOME
   export JAVA_HOME=/opt/homebrew/opt/openjdk@17
   ```

2. **Install Maven:**
   ```bash
   brew install maven
   ```

3. **Run in Dev Mode (with hot reload):**
   ```bash
   cd src/truck-poller-camel
   mvn quarkus:dev
   ```

### Running Python Services Locally

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run:**
   ```bash
   python poller.py  # or consumer.py
   ```

### Debugging on OpenShift

```bash
# View logs
oc logs -f deployment/truck-poller-camel

# Get pod shell
oc rsh deployment/truck-poller-camel

# Check environment variables
oc set env deployment/truck-poller-camel --list
```

