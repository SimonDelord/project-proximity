"""
Truck Data Models for BHP Proximity Detection System

Comprehensive data models representing all truck parameters
for mining fleet operations and proximity monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import json


# ============================================================================
# ENUMS
# ============================================================================

class TruckModel(Enum):
    """Supported truck models in the fleet."""
    CAT_797F = "Caterpillar 797F"
    CAT_793F = "Caterpillar 793F"
    CAT_789D = "Caterpillar 789D"
    KOMATSU_980E = "Komatsu 980E-5"
    KOMATSU_930E = "Komatsu 930E-5"
    KOMATSU_830E = "Komatsu 830E-5"
    LIEBHERR_T284 = "Liebherr T 284"
    LIEBHERR_T264 = "Liebherr T 264"
    HITACHI_EH5000 = "Hitachi EH5000AC-3"


class LoadStatus(Enum):
    """Current load status of the truck."""
    EMPTY = "empty"
    LOADING = "loading"
    LOADED = "loaded"
    DUMPING = "dumping"
    UNKNOWN = "unknown"


class OperatingMode(Enum):
    """Truck operating mode."""
    MANUAL = "manual"
    AUTONOMOUS = "autonomous"
    REMOTE = "remote"
    MAINTENANCE = "maintenance"
    STANDBY = "standby"


class TrayPosition(Enum):
    """Position of the truck tray/bed."""
    LOWERED = "lowered"
    RAISING = "raising"
    RAISED = "raised"
    LOWERING = "lowering"


class ZoneType(Enum):
    """Type of operational zone."""
    PIT = "pit"
    HAUL_ROAD = "haul_road"
    DUMP = "dump"
    STOCKPILE = "stockpile"
    WORKSHOP = "workshop"
    FUEL_BAY = "fuel_bay"
    WASH_BAY = "wash_bay"
    PARKING = "parking"
    EXCLUSION = "exclusion"


class AlertSeverity(Enum):
    """Severity level for alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TruckIdentification:
    """Core identification parameters for a truck."""
    truck_id: str
    asset_number: str
    vin: Optional[str] = None
    model: TruckModel = TruckModel.CAT_797F
    fleet_id: str = "default"
    site_id: str = "default"
    firmware_version: str = "1.0.0"
    hardware_version: str = "1.0.0"
    registration_date: Optional[datetime] = None


@dataclass
class GPSLocation:
    """GPS location data."""
    latitude: float
    longitude: float
    altitude: float = 0.0
    heading: float = 0.0  # degrees (0-360)
    speed: float = 0.0    # km/h
    accuracy: float = 1.0  # meters
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "heading": self.heading,
            "speed": self.speed,
            "accuracy": self.accuracy,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EngineMetrics:
    """Engine and powertrain parameters."""
    engine_hours: float = 0.0
    engine_rpm: int = 0
    engine_temp: float = 0.0          # Celsius
    oil_pressure: float = 0.0          # kPa
    oil_temp: float = 0.0              # Celsius
    coolant_temp: float = 0.0          # Celsius
    transmission_temp: float = 0.0     # Celsius
    fuel_level: float = 100.0          # percentage
    fuel_consumption_rate: float = 0.0 # L/hr
    throttle_position: float = 0.0     # percentage
    ignition_on: bool = False


@dataclass
class PayloadData:
    """Load and payload information."""
    payload_weight: float = 0.0        # tonnes
    max_payload: float = 400.0         # tonnes (depends on truck model)
    load_status: LoadStatus = LoadStatus.EMPTY
    tray_position: TrayPosition = TrayPosition.LOWERED
    cycle_count: int = 0               # loads this shift
    total_tonnes_hauled: float = 0.0   # this shift


@dataclass 
class TyrePressure:
    """Individual tyre data."""
    position: str              # e.g., "front_left", "rear_outer_left"
    pressure: float            # kPa
    temperature: float         # Celsius
    wear_percentage: float = 100.0
    last_checked: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BrakeSystem:
    """Brake and retarder information."""
    brake_temp_front: float = 0.0      # Celsius
    brake_temp_rear: float = 0.0       # Celsius
    retarder_active: bool = False
    retarder_temp: float = 0.0         # Celsius
    brake_wear_front: float = 100.0    # percentage remaining
    brake_wear_rear: float = 100.0     # percentage remaining
    parking_brake_engaged: bool = True
    emergency_brake_active: bool = False


@dataclass
class HydraulicSystem:
    """Hydraulic system parameters."""
    hydraulic_pressure: float = 0.0    # kPa
    hydraulic_temp: float = 0.0        # Celsius
    hydraulic_fluid_level: float = 100.0  # percentage
    steering_pressure: float = 0.0     # kPa


@dataclass
class ElectricalSystem:
    """Electrical system parameters."""
    battery_voltage: float = 24.0      # Volts
    alternator_output: float = 0.0     # Amps
    main_power_on: bool = False
    auxiliary_power_on: bool = False
    communication_status: bool = True  # online/offline


@dataclass
class SafetyStatus:
    """Safety-related parameters."""
    seatbelt_fastened: bool = False
    operator_id: Optional[str] = None
    operator_logged_in: bool = False
    fatigue_score: float = 100.0       # 0-100, higher is better
    emergency_stop_active: bool = False
    horn_active: bool = False
    lights_on: bool = False
    beacon_active: bool = False
    fire_suppression_armed: bool = True


@dataclass
class ProximityData:
    """Proximity detection data for collision avoidance."""
    proximity_system_active: bool = True
    nearest_vehicle_id: Optional[str] = None
    nearest_vehicle_distance: Optional[float] = None  # meters
    nearest_vehicle_bearing: Optional[float] = None   # degrees
    collision_warning_active: bool = False
    collision_warning_level: AlertSeverity = AlertSeverity.INFO
    vehicles_in_range: List[str] = field(default_factory=list)
    zone_violations: List[str] = field(default_factory=list)
    last_proximity_scan: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ZoneInfo:
    """Current zone and geofence information."""
    current_zone_id: Optional[str] = None
    current_zone_type: ZoneType = ZoneType.HAUL_ROAD
    current_zone_name: Optional[str] = None
    speed_limit: float = 60.0          # km/h for current zone
    authorized_for_zone: bool = True
    time_in_zone: float = 0.0          # seconds


@dataclass
class MaintenanceInfo:
    """Maintenance and service information."""
    last_service_date: Optional[datetime] = None
    last_service_hours: float = 0.0
    next_service_due_hours: float = 500.0
    hours_until_service: float = 500.0
    active_fault_codes: List[str] = field(default_factory=list)
    warning_lights: List[str] = field(default_factory=list)
    maintenance_mode: bool = False


@dataclass
class OperationalMetrics:
    """Operational statistics."""
    odometer: float = 0.0              # km
    trip_distance: float = 0.0         # km (current trip)
    operating_mode: OperatingMode = OperatingMode.MANUAL
    shift_id: Optional[str] = None
    shift_start_time: Optional[datetime] = None
    total_idle_time: float = 0.0       # seconds this shift
    total_moving_time: float = 0.0     # seconds this shift
    efficiency_score: float = 0.0      # percentage


# ============================================================================
# MAIN TRUCK MODEL
# ============================================================================

@dataclass
class Truck:
    """
    Complete truck data model combining all subsystems.
    
    This is the primary model for representing a mining haul truck
    with all its telemetry, safety, and operational data.
    """
    # Core identification
    identification: TruckIdentification
    
    # Location and movement
    location: GPSLocation
    
    # Vehicle systems
    engine: EngineMetrics = field(default_factory=EngineMetrics)
    payload: PayloadData = field(default_factory=PayloadData)
    brakes: BrakeSystem = field(default_factory=BrakeSystem)
    hydraulics: HydraulicSystem = field(default_factory=HydraulicSystem)
    electrical: ElectricalSystem = field(default_factory=ElectricalSystem)
    
    # Tyres (6 tyres for typical haul truck)
    tyres: List[TyrePressure] = field(default_factory=list)
    
    # Safety and proximity
    safety: SafetyStatus = field(default_factory=SafetyStatus)
    proximity: ProximityData = field(default_factory=ProximityData)
    
    # Zone and operations
    zone: ZoneInfo = field(default_factory=ZoneInfo)
    operations: OperationalMetrics = field(default_factory=OperationalMetrics)
    maintenance: MaintenanceInfo = field(default_factory=MaintenanceInfo)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_quality_score: float = 100.0  # 0-100
    
    def to_dict(self) -> dict:
        """Convert truck data to dictionary for serialization."""
        from dataclasses import asdict
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert truck data to JSON string."""
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            return obj
        
        data = self.to_dict()
        return json.dumps(data, default=serialize, indent=2)
    
    @property
    def truck_id(self) -> str:
        """Convenience property for truck ID."""
        return self.identification.truck_id
    
    @property
    def is_moving(self) -> bool:
        """Check if truck is currently moving."""
        return self.location.speed > 0.5
    
    @property
    def is_loaded(self) -> bool:
        """Check if truck is carrying a load."""
        return self.payload.load_status == LoadStatus.LOADED
    
    @property
    def has_active_warnings(self) -> bool:
        """Check if there are any active warnings."""
        return (
            len(self.maintenance.active_fault_codes) > 0 or
            len(self.maintenance.warning_lights) > 0 or
            self.proximity.collision_warning_active
        )


# ============================================================================
# PROXIMITY EVENT MODEL
# ============================================================================

@dataclass
class ProximityEvent:
    """
    Model for proximity detection events between vehicles.
    Used for logging and alerting when vehicles come within
    defined safety distances.
    """
    event_id: str
    timestamp: datetime
    
    # Primary vehicle
    truck_id: str
    truck_location: GPSLocation
    truck_speed: float
    truck_heading: float
    
    # Other vehicle
    other_vehicle_id: str
    other_vehicle_type: str  # truck, light_vehicle, personnel, etc.
    other_vehicle_location: GPSLocation
    other_vehicle_speed: float
    other_vehicle_heading: float
    
    # Proximity details
    distance: float              # meters
    closing_speed: float         # m/s (positive = approaching)
    time_to_collision: Optional[float] = None  # seconds
    
    # Alert details
    severity: AlertSeverity = AlertSeverity.INFO
    alert_triggered: bool = False
    alert_acknowledged: bool = False
    
    # Zone context
    zone_id: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    
    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_default_truck(truck_id: str, asset_number: str) -> Truck:
    """Create a truck instance with default values."""
    return Truck(
        identification=TruckIdentification(
            truck_id=truck_id,
            asset_number=asset_number,
            registration_date=datetime.utcnow()
        ),
        location=GPSLocation(
            latitude=-23.3617,  # Default to West Angelas area
            longitude=118.7083,
            altitude=600.0
        ),
        tyres=[
            TyrePressure(position="front_left", pressure=700.0, temperature=45.0),
            TyrePressure(position="front_right", pressure=700.0, temperature=45.0),
            TyrePressure(position="rear_inner_left", pressure=700.0, temperature=45.0),
            TyrePressure(position="rear_inner_right", pressure=700.0, temperature=45.0),
            TyrePressure(position="rear_outer_left", pressure=700.0, temperature=45.0),
            TyrePressure(position="rear_outer_right", pressure=700.0, temperature=45.0),
        ]
    )


if __name__ == "__main__":
    # Example usage
    truck = create_default_truck("TRK-001", "BHP-WA-001")
    truck.engine.engine_rpm = 1800
    truck.engine.ignition_on = True
    truck.location.speed = 35.5
    truck.payload.load_status = LoadStatus.LOADED
    truck.payload.payload_weight = 320.0
    
    print(f"Truck: {truck.truck_id}")
    print(f"Moving: {truck.is_moving}")
    print(f"Loaded: {truck.is_loaded}")
    print(f"\nFull JSON:\n{truck.to_json()}")

