# Sample Trucks Fleet - 10 Truck API Instances

This folder contains deployment manifests for 10 individual truck API instances, each with unique configurations.

## Truck Fleet Overview

| Truck | Truck ID | Firmware Version | Zone | Model |
|-------|----------|------------------|------|-------|
| truck-01 | TRK-001 | 2.4.1-build.2847 | Main Pit North | CAT 797F |
| truck-02 | TRK-002 | 2.4.1-build.2850 | Main Pit North | CAT 797F |
| truck-03 | TRK-003 | 2.4.1-build.2853 | Main Pit South | Komatsu 930E |
| truck-04 | TRK-004 | 2.4.1-build.2860 | Main Pit South | Komatsu 930E |
| truck-05 | TRK-005 | 3.0.0-build.3001 | North Haul Road | Liebherr T284 |
| truck-06 | TRK-006 | 3.0.0-build.3005 | North Haul Road | Liebherr T284 |
| truck-07 | TRK-007 | 3.0.0-build.3010 | Waste Dump Alpha | CAT 797F |
| truck-08 | TRK-008 | 3.1.2-build.3120 | Waste Dump Alpha | Hitachi EH5000 |
| truck-09 | TRK-009 | 3.1.2-build.3125 | Loading Bay East | Belaz 75710 |
| truck-10 | TRK-010 | 3.1.2-build.3130 | Loading Bay East | Belaz 75710 |

## Firmware Versions

Three firmware versions are deployed across the fleet:

- **v2.4.1** (Trucks 1-4): Legacy firmware, hardware v1.2.0
- **v3.0.0** (Trucks 5-7): Current stable, hardware v1.3.0
- **v3.1.2** (Trucks 8-10): Latest release, hardware v1.4.0

## Deployment

### Prerequisites

1. OpenShift cluster access
2. `trucks` namespace exists
3. Container image built and pushed to registry

### Build the Image

From the project root:

```bash
# Create build config in trucks namespace
oc project trucks
oc new-build --name=sample-truck --binary --strategy=docker -n trucks

# Build from project root
oc start-build sample-truck --from-dir=. --follow -n trucks
```

### Deploy All Trucks

```bash
# Deploy all 10 trucks
oc apply -f configs/sample-trucks/

# Or deploy individually
oc apply -f configs/sample-trucks/truck-01-deployment.yaml
```

### Verify Deployment

```bash
# Check all truck pods
oc get pods -n trucks -l app.kubernetes.io/part-of=sample-trucks

# Check routes
oc get routes -n trucks

# Test a truck endpoint
curl https://truck-01-trucks.apps.<cluster>/trucks/sample
```

## Configuration

Each truck is configured via environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TRUCK_ID` | Unique truck identifier | TRK-001 |
| `TRUCK_NUMBER` | Numeric truck number (1-10) | 1 |
| `FLEET_ID` | Fleet identifier | BHP-WA-001 |
| `FIRMWARE_VERSION` | Firmware version string | 2.4.1-build.2847 |
| `HARDWARE_VERSION` | Hardware version string | 1.2.0 |

## API Endpoints

Each truck exposes:

- `GET /` - Truck info
- `GET /health` - Health check
- `GET /trucks/sample` - Current telemetry data

## Data Variations

Each truck generates realistic but varied data:

- **Location**: Unique GPS coordinates per zone
- **Engine metrics**: Varied RPM, temperature, fuel levels
- **Payload**: Different load statuses (Empty, Loading, Loaded, Dumping)
- **Operators**: Assigned to different operators
- **Zones**: Working in different mine areas

