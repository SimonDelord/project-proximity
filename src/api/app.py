"""
BHP Proximity Truck API
Simple HTTP server exposing truck parameters on port 80.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from enum import Enum
import sys
import os

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

app = FastAPI(
    title="BHP Proximity Truck API",
    description="API for accessing mining truck parameters and telemetry data",
    version="1.0.0",
)


def enum_to_list(enum_class: type) -> list:
    """Convert an Enum class to a list of its values."""
    return [{"name": e.name, "value": e.value} for e in enum_class]


def get_dataclass_fields(dataclass_type: type) -> dict:
    """Extract field information from a dataclass."""
    import dataclasses
    fields = {}
    for field in dataclasses.fields(dataclass_type):
        field_type = str(field.type)
        # Clean up type string
        field_type = field_type.replace("typing.", "").replace("<class '", "").replace("'>", "")
        fields[field.name] = {
            "type": field_type,
            "has_default": field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING
        }
    return fields


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "BHP Proximity Truck API",
        "version": "1.0.0",
        "description": "Mining fleet truck parameters API",
        "endpoints": {
            "/": "This information",
            "/health": "Health check",
            "/trucks/schema": "Complete truck data model schema",
            "/trucks/models": "Available truck models",
            "/trucks/enums": "All enum types and values",
            "/trucks/sample": "Sample truck data",
            "/trucks/parameters": "Flat list of all truck parameters",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/trucks/models")
async def get_truck_models():
    """Get list of supported truck models."""
    return {
        "truck_models": enum_to_list(TruckModel),
        "count": len(TruckModel)
    }


@app.get("/trucks/enums")
async def get_all_enums():
    """Get all enum types used in truck parameters."""
    return {
        "TruckModel": enum_to_list(TruckModel),
        "LoadStatus": enum_to_list(LoadStatus),
        "OperatingMode": enum_to_list(OperatingMode),
        "TrayPosition": enum_to_list(TrayPosition),
        "ZoneType": enum_to_list(ZoneType),
        "AlertSeverity": enum_to_list(AlertSeverity),
    }


@app.get("/trucks/schema")
async def get_truck_schema():
    """Get the complete truck data model schema."""
    return {
        "Truck": {
            "description": "Complete truck data model combining all subsystems",
            "subsystems": {
                "identification": get_dataclass_fields(TruckIdentification),
                "location": get_dataclass_fields(GPSLocation),
                "engine": get_dataclass_fields(EngineMetrics),
                "payload": get_dataclass_fields(PayloadData),
                "brakes": get_dataclass_fields(BrakeSystem),
                "hydraulics": get_dataclass_fields(HydraulicSystem),
                "electrical": get_dataclass_fields(ElectricalSystem),
                "safety": get_dataclass_fields(SafetyStatus),
                "proximity": get_dataclass_fields(ProximityData),
                "zone": get_dataclass_fields(ZoneInfo),
                "operations": get_dataclass_fields(OperationalMetrics),
                "maintenance": get_dataclass_fields(MaintenanceInfo),
            },
            "tyre_schema": get_dataclass_fields(TyrePressure),
        }
    }


@app.get("/trucks/parameters")
async def get_all_parameters():
    """Get a flat list of all truck parameters with descriptions."""
    parameters = []
    
    # Helper to add params from a dataclass
    def add_params(category: str, dataclass_type: type):
        fields = get_dataclass_fields(dataclass_type)
        for name, info in fields.items():
            parameters.append({
                "category": category,
                "parameter": name,
                "type": info["type"],
                "has_default": info["has_default"]
            })
    
    add_params("identification", TruckIdentification)
    add_params("location", GPSLocation)
    add_params("engine", EngineMetrics)
    add_params("payload", PayloadData)
    add_params("brakes", BrakeSystem)
    add_params("hydraulics", HydraulicSystem)
    add_params("electrical", ElectricalSystem)
    add_params("safety", SafetyStatus)
    add_params("proximity", ProximityData)
    add_params("zone", ZoneInfo)
    add_params("operations", OperationalMetrics)
    add_params("maintenance", MaintenanceInfo)
    add_params("tyres", TyrePressure)
    
    return {
        "total_parameters": len(parameters),
        "parameters": parameters
    }


@app.get("/trucks/sample")
async def get_sample_truck():
    """Get a sample truck with realistic data."""
    truck = create_default_truck("TRK-001", "BHP-WA-001")
    
    # Set firmware and hardware versions
    truck.identification.firmware_version = "2.4.1-build.2847"
    truck.identification.hardware_version = "1.2.0"
    
    # Populate with sample operational data
    truck.engine.engine_rpm = 1800
    truck.engine.engine_temp = 92.5
    truck.engine.oil_pressure = 450.0
    truck.engine.coolant_temp = 88.0
    truck.engine.fuel_level = 75.5
    truck.engine.ignition_on = True
    
    truck.location.speed = 42.5
    truck.location.heading = 127.5
    
    truck.payload.load_status = LoadStatus.LOADED
    truck.payload.payload_weight = 320.0
    truck.payload.cycle_count = 8
    truck.payload.total_tonnes_hauled = 2560.0
    
    truck.safety.operator_id = "OP-12345"
    truck.safety.operator_logged_in = True
    truck.safety.seatbelt_fastened = True
    truck.safety.lights_on = True
    truck.safety.beacon_active = True
    
    truck.operations.operating_mode = OperatingMode.MANUAL
    truck.operations.shift_id = "SHIFT-2024-001"
    truck.operations.odometer = 125430.5
    
    truck.zone.current_zone_id = "ZONE-PIT-03"
    truck.zone.current_zone_type = ZoneType.PIT
    truck.zone.current_zone_name = "Main Pit Area 3"
    truck.zone.speed_limit = 40.0
    
    # Convert to JSON-serializable dict
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return obj
    
    import json
    data = json.loads(truck.to_json())
    
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

