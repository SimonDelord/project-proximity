"""
BHP Proximity - Configurable Truck API
Individual truck instance with configurable parameters via environment variables.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from enum import Enum
import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.truck import (
    Truck,
    TruckIdentification,
    GPSLocation,
    EngineMetrics,
    PayloadData,
    BrakeSystem,
    HydraulicSystem,
    ElectricalSystem,
    SafetyStatus,
    ProximityData,
    ZoneInfo,
    OperationalMetrics,
    MaintenanceInfo,
    TyrePressure,
    TruckModel,
    LoadStatus,
    OperatingMode,
    TrayPosition,
    ZoneType,
    AlertSeverity,
    create_default_truck,
)

# ============================================================
# TRUCK CONFIGURATION FROM ENVIRONMENT VARIABLES
# ============================================================
TRUCK_ID = os.getenv('TRUCK_ID', 'TRK-001')
TRUCK_NUMBER = int(os.getenv('TRUCK_NUMBER', '1'))
FLEET_ID = os.getenv('FLEET_ID', 'BHP-WA-001')
FIRMWARE_VERSION = os.getenv('FIRMWARE_VERSION', '2.4.1-build.2847')
HARDWARE_VERSION = os.getenv('HARDWARE_VERSION', '1.2.0')

# Truck-specific variations based on truck number
TRUCK_PROFILES = {
    1: {"zone": "PIT-01", "zone_name": "Main Pit North", "model": TruckModel.CAT_797F, "base_lat": -23.3601, "base_lon": 119.7310},
    2: {"zone": "PIT-01", "zone_name": "Main Pit North", "model": TruckModel.CAT_797F, "base_lat": -23.3615, "base_lon": 119.7325},
    3: {"zone": "PIT-02", "zone_name": "Main Pit South", "model": TruckModel.KOMATSU_930E, "base_lat": -23.3680, "base_lon": 119.7290},
    4: {"zone": "PIT-02", "zone_name": "Main Pit South", "model": TruckModel.KOMATSU_930E, "base_lat": -23.3695, "base_lon": 119.7305},
    5: {"zone": "HAUL-01", "zone_name": "North Haul Road", "model": TruckModel.LIEBHERR_T284, "base_lat": -23.3520, "base_lon": 119.7450},
    6: {"zone": "HAUL-01", "zone_name": "North Haul Road", "model": TruckModel.LIEBHERR_T284, "base_lat": -23.3535, "base_lon": 119.7465},
    7: {"zone": "DUMP-01", "zone_name": "Waste Dump Alpha", "model": TruckModel.CAT_797F, "base_lat": -23.3400, "base_lon": 119.7600},
    8: {"zone": "DUMP-01", "zone_name": "Waste Dump Alpha", "model": TruckModel.HITACHI_EH5000, "base_lat": -23.3415, "base_lon": 119.7615},
    9: {"zone": "LOAD-01", "zone_name": "Loading Bay East", "model": TruckModel.KOMATSU_980E, "base_lat": -23.3750, "base_lon": 119.7200},
    10: {"zone": "LOAD-01", "zone_name": "Loading Bay East", "model": TruckModel.CAT_793F, "base_lat": -23.3765, "base_lon": 119.7215},
}

app = FastAPI(
    title=f"BHP Truck API - {TRUCK_ID}",
    description=f"Telemetry API for truck {TRUCK_ID}",
    version="1.0.0",
)


def get_truck_profile(truck_num: int) -> dict:
    """Get truck profile based on truck number, with defaults."""
    return TRUCK_PROFILES.get(truck_num, TRUCK_PROFILES[1])


def add_realistic_variation(base_value: float, variance_percent: float = 5.0) -> float:
    """Add realistic variation to a base value."""
    variance = base_value * (variance_percent / 100.0)
    return round(base_value + random.uniform(-variance, variance), 2)


def generate_truck_data() -> dict:
    """Generate truck telemetry with unique data based on truck configuration."""
    profile = get_truck_profile(TRUCK_NUMBER)
    
    truck = create_default_truck(TRUCK_ID, FLEET_ID)
    
    # Set identification
    truck.identification.truck_id = TRUCK_ID
    truck.identification.fleet_id = FLEET_ID
    truck.identification.firmware_version = FIRMWARE_VERSION
    truck.identification.hardware_version = HARDWARE_VERSION
    truck.identification.model = profile["model"]
    
    # Set GPS location with variation
    truck.location.latitude = add_realistic_variation(profile["base_lat"], 0.01)
    truck.location.longitude = add_realistic_variation(profile["base_lon"], 0.01)
    truck.location.altitude = add_realistic_variation(450.0 + (TRUCK_NUMBER * 5), 2.0)
    truck.location.speed = add_realistic_variation(35.0 + (TRUCK_NUMBER % 3) * 5, 15.0)
    truck.location.heading = add_realistic_variation(90.0 + (TRUCK_NUMBER * 36), 10.0) % 360
    truck.location.gps_quality = random.choice([4, 5, 5, 5])  # Mostly good quality
    truck.location.satellites_visible = random.randint(8, 14)
    
    # Set engine metrics with variation per truck
    base_rpm = 1600 + (TRUCK_NUMBER * 50)
    truck.engine.engine_rpm = int(add_realistic_variation(base_rpm, 8.0))
    truck.engine.engine_temp = add_realistic_variation(90.0 + (TRUCK_NUMBER % 3) * 2, 5.0)
    truck.engine.oil_pressure = add_realistic_variation(440.0 + (TRUCK_NUMBER * 5), 3.0)
    truck.engine.coolant_temp = add_realistic_variation(85.0 + (TRUCK_NUMBER % 4) * 2, 4.0)
    truck.engine.fuel_level = add_realistic_variation(70.0 - (TRUCK_NUMBER * 4), 10.0)
    truck.engine.fuel_level = max(15.0, min(95.0, truck.engine.fuel_level))  # Clamp
    truck.engine.def_level = add_realistic_variation(80.0 - (TRUCK_NUMBER * 3), 8.0)
    truck.engine.def_level = max(20.0, min(95.0, truck.engine.def_level))
    truck.engine.ignition_on = True
    truck.engine.engine_hours = 12500.0 + (TRUCK_NUMBER * 850)
    
    # Set payload data
    load_statuses = [LoadStatus.EMPTY, LoadStatus.LOADING, LoadStatus.LOADED, LoadStatus.DUMPING]
    truck.payload.load_status = load_statuses[TRUCK_NUMBER % 4]
    
    if truck.payload.load_status == LoadStatus.LOADED:
        truck.payload.payload_weight = add_realistic_variation(300.0 + (TRUCK_NUMBER * 10), 5.0)
    elif truck.payload.load_status == LoadStatus.LOADING:
        truck.payload.payload_weight = add_realistic_variation(150.0 + (TRUCK_NUMBER * 5), 10.0)
    elif truck.payload.load_status == LoadStatus.DUMPING:
        truck.payload.payload_weight = add_realistic_variation(50.0, 20.0)
    else:
        truck.payload.payload_weight = 0.0
    
    truck.payload.cycle_count = 5 + (TRUCK_NUMBER * 2)
    truck.payload.total_tonnes_hauled = truck.payload.cycle_count * 310.0
    
    # Set brake system
    truck.brakes.brake_pressure_front = add_realistic_variation(2800.0, 3.0)
    truck.brakes.brake_pressure_rear = add_realistic_variation(2750.0, 3.0)
    truck.brakes.retarder_active = TRUCK_NUMBER % 3 == 0
    truck.brakes.retarder_temp = add_realistic_variation(180.0 if truck.brakes.retarder_active else 45.0, 10.0)
    truck.brakes.parking_brake_engaged = False
    truck.brakes.brake_wear_front = add_realistic_variation(25.0 + (TRUCK_NUMBER * 3), 15.0)
    truck.brakes.brake_wear_rear = add_realistic_variation(30.0 + (TRUCK_NUMBER * 3), 15.0)
    
    # Set hydraulic system
    truck.hydraulics.hydraulic_pressure = add_realistic_variation(3200.0, 2.0)
    truck.hydraulics.hydraulic_temp = add_realistic_variation(65.0 + (TRUCK_NUMBER % 4) * 3, 5.0)
    truck.hydraulics.hydraulic_level = add_realistic_variation(92.0, 3.0)
    truck.hydraulics.steering_pressure = add_realistic_variation(2400.0, 3.0)
    tray_positions = [TrayPosition.LOWERED, TrayPosition.RAISING, TrayPosition.RAISED, TrayPosition.LOWERING]
    truck.hydraulics.tray_position = tray_positions[TRUCK_NUMBER % 4]
    truck.hydraulics.tray_angle = {TrayPosition.LOWERED: 0.0, TrayPosition.RAISING: 25.0, TrayPosition.RAISED: 55.0, TrayPosition.LOWERING: 30.0}[truck.hydraulics.tray_position]
    
    # Set electrical system
    truck.electrical.battery_voltage = add_realistic_variation(24.2 + (TRUCK_NUMBER % 3) * 0.2, 2.0)
    truck.electrical.alternator_output = add_realistic_variation(28.5, 1.5)
    truck.electrical.electrical_load = add_realistic_variation(45.0 + (TRUCK_NUMBER * 2), 10.0)
    
    # Set safety status
    operator_ids = ["OP-1001", "OP-1002", "OP-1003", "OP-1004", "OP-1005"]
    truck.safety.operator_id = operator_ids[(TRUCK_NUMBER - 1) % 5]
    truck.safety.operator_logged_in = True
    truck.safety.fatigue_level = random.choice([0, 0, 0, 1, 1, 2])  # Mostly 0
    truck.safety.seatbelt_fastened = True
    truck.safety.door_closed = True
    truck.safety.lights_on = True
    truck.safety.beacon_active = True
    truck.safety.horn_functional = True
    truck.safety.fire_suppression_armed = True
    truck.safety.emergency_stop_status = False
    
    # Set proximity data
    nearby_trucks = [f"TRK-{str(i).zfill(3)}" for i in range(1, 11) if i != TRUCK_NUMBER]
    truck.proximity.nearest_vehicle_id = random.choice(nearby_trucks)
    truck.proximity.nearest_vehicle_distance = add_realistic_variation(25.0 + (TRUCK_NUMBER * 3), 30.0)
    truck.proximity.collision_warning_active = truck.proximity.nearest_vehicle_distance < 10.0
    truck.proximity.vehicles_in_range = random.randint(1, 4)
    
    # Set zone info
    zone_types = {
        "PIT": ZoneType.PIT,
        "HAUL": ZoneType.HAUL_ROAD,
        "DUMP": ZoneType.DUMP,
        "LOAD": ZoneType.STOCKPILE,  # Use STOCKPILE for loading areas
    }
    zone_prefix = profile["zone"].split("-")[0]
    truck.zone.current_zone_id = f"ZONE-{profile['zone']}"
    truck.zone.current_zone_type = zone_types.get(zone_prefix, ZoneType.PIT)
    truck.zone.current_zone_name = profile["zone_name"]
    truck.zone.speed_limit = {ZoneType.PIT: 25.0, ZoneType.HAUL_ROAD: 45.0, ZoneType.DUMP: 15.0, ZoneType.STOCKPILE: 10.0}[truck.zone.current_zone_type]
    truck.zone.in_restricted_area = False
    
    # Set operational metrics
    truck.operations.odometer = 100000.0 + (TRUCK_NUMBER * 15000)
    truck.operations.operating_mode = OperatingMode.MANUAL
    truck.operations.shift_id = f"SHIFT-{datetime.now().strftime('%Y%m%d')}-{((TRUCK_NUMBER - 1) // 4) + 1}"
    truck.operations.current_task = {
        LoadStatus.EMPTY: "Returning to loader",
        LoadStatus.LOADING: "Being loaded",
        LoadStatus.LOADED: "Hauling to dump",
        LoadStatus.DUMPING: "Dumping load",
    }[truck.payload.load_status]
    
    # Set maintenance info
    truck.maintenance.next_service_hours = 500 - (TRUCK_NUMBER * 30)
    truck.maintenance.last_inspection = datetime.now().replace(day=max(1, datetime.now().day - TRUCK_NUMBER))
    truck.maintenance.tyre_hours_remaining = [
        1500 - (TRUCK_NUMBER * 50),
        1520 - (TRUCK_NUMBER * 50),
        1480 - (TRUCK_NUMBER * 50),
        1510 - (TRUCK_NUMBER * 50),
        1490 - (TRUCK_NUMBER * 50),
        1500 - (TRUCK_NUMBER * 50),
    ]
    
    # Set tyre pressures
    base_pressure = 700.0
    for i, tyre in enumerate(truck.tyres):
        tyre.pressure = add_realistic_variation(base_pressure + (i * 5), 2.0)
        tyre.temperature = add_realistic_variation(55.0 + (TRUCK_NUMBER % 3) * 3, 8.0)
    
    return truck


@app.get("/")
async def root():
    """Root endpoint with truck information."""
    return {
        "service": f"BHP Truck API - {TRUCK_ID}",
        "truck_id": TRUCK_ID,
        "truck_number": TRUCK_NUMBER,
        "fleet_id": FLEET_ID,
        "firmware_version": FIRMWARE_VERSION,
        "endpoints": {
            "/": "This information",
            "/health": "Health check",
            "/trucks/sample": "Current truck telemetry data",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "truck_id": TRUCK_ID,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/trucks/sample")
async def get_truck_data():
    """Get current truck telemetry data with realistic values."""
    truck = generate_truck_data()
    
    import json
    data = json.loads(truck.to_json())
    
    # Add metadata
    data["_metadata"] = {
        "generated_at": datetime.utcnow().isoformat(),
        "truck_number": TRUCK_NUMBER,
        "api_version": "1.0.0"
    }
    
    return data


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', '8080'))
    uvicorn.run(app, host="0.0.0.0", port=port)

