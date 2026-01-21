-- ============================================================================
-- BHP Project Proximity - Database Schema
-- Mining Fleet Truck Parameters
-- ============================================================================

-- Enable UUID extension if using PostgreSQL
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS truck_models (
    model_id VARCHAR(50) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    max_payload_tonnes DECIMAL(10,2),
    empty_weight_tonnes DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO truck_models (model_id, model_name, manufacturer, max_payload_tonnes, empty_weight_tonnes) VALUES
    ('CAT_797F', 'Caterpillar 797F', 'Caterpillar', 400.0, 260.0),
    ('CAT_793F', 'Caterpillar 793F', 'Caterpillar', 250.0, 165.0),
    ('CAT_789D', 'Caterpillar 789D', 'Caterpillar', 195.0, 130.0),
    ('KOMATSU_980E', 'Komatsu 980E-5', 'Komatsu', 400.0, 270.0),
    ('KOMATSU_930E', 'Komatsu 930E-5', 'Komatsu', 320.0, 215.0),
    ('KOMATSU_830E', 'Komatsu 830E-5', 'Komatsu', 255.0, 170.0),
    ('LIEBHERR_T284', 'Liebherr T 284', 'Liebherr', 400.0, 260.0),
    ('HITACHI_EH5000', 'Hitachi EH5000AC-3', 'Hitachi', 326.0, 220.0);

CREATE TABLE IF NOT EXISTS zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50) NOT NULL,  -- pit, haul_road, dump, stockpile, workshop, etc.
    site_id VARCHAR(50) NOT NULL,
    speed_limit_kmh DECIMAL(5,2) DEFAULT 60.0,
    is_active BOOLEAN DEFAULT TRUE,
    geofence_polygon TEXT,  -- GeoJSON polygon
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sites (
    site_id VARCHAR(50) PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    site_location VARCHAR(200),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    timezone VARCHAR(50) DEFAULT 'Australia/Perth',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fleets (
    fleet_id VARCHAR(50) PRIMARY KEY,
    fleet_name VARCHAR(100) NOT NULL,
    site_id VARCHAR(50) REFERENCES sites(site_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CORE TRUCK TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS trucks (
    truck_id VARCHAR(50) PRIMARY KEY,
    asset_number VARCHAR(50) UNIQUE NOT NULL,
    vin VARCHAR(50),
    model_id VARCHAR(50) REFERENCES truck_models(model_id),
    fleet_id VARCHAR(50) REFERENCES fleets(fleet_id),
    site_id VARCHAR(50) REFERENCES sites(site_id),
    firmware_version VARCHAR(20) DEFAULT '1.0.0',
    hardware_version VARCHAR(20) DEFAULT '1.0.0',
    registration_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- REAL-TIME TELEMETRY TABLES (Time-series data)
-- ============================================================================

-- GPS and Location Data
CREATE TABLE IF NOT EXISTS truck_locations (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    altitude DECIMAL(8,2),
    heading DECIMAL(5,2),          -- degrees 0-360
    speed DECIMAL(6,2),            -- km/h
    accuracy DECIMAL(5,2),         -- meters
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_locations_truck_time ON truck_locations(truck_id, timestamp DESC);

-- Engine Metrics
CREATE TABLE IF NOT EXISTS truck_engine_metrics (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    engine_hours DECIMAL(10,2),
    engine_rpm INT,
    engine_temp DECIMAL(5,2),       -- Celsius
    oil_pressure DECIMAL(7,2),      -- kPa
    oil_temp DECIMAL(5,2),          -- Celsius
    coolant_temp DECIMAL(5,2),      -- Celsius
    transmission_temp DECIMAL(5,2), -- Celsius
    fuel_level DECIMAL(5,2),        -- percentage
    fuel_consumption_rate DECIMAL(6,2), -- L/hr
    throttle_position DECIMAL(5,2), -- percentage
    ignition_on BOOLEAN,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_engine_truck_time ON truck_engine_metrics(truck_id, timestamp DESC);

-- Payload Data
CREATE TABLE IF NOT EXISTS truck_payload (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    payload_weight DECIMAL(8,2),    -- tonnes
    load_status VARCHAR(20),        -- empty, loading, loaded, dumping
    tray_position VARCHAR(20),      -- lowered, raising, raised, lowering
    cycle_count INT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_payload_truck_time ON truck_payload(truck_id, timestamp DESC);

-- Tyre Data
CREATE TABLE IF NOT EXISTS truck_tyres (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    tyre_position VARCHAR(30) NOT NULL,  -- front_left, rear_inner_left, etc.
    pressure DECIMAL(6,2),          -- kPa
    temperature DECIMAL(5,2),       -- Celsius
    wear_percentage DECIMAL(5,2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_tyres_truck_time ON truck_tyres(truck_id, timestamp DESC);

-- Brake System
CREATE TABLE IF NOT EXISTS truck_brakes (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    brake_temp_front DECIMAL(5,2),  -- Celsius
    brake_temp_rear DECIMAL(5,2),   -- Celsius
    retarder_active BOOLEAN,
    retarder_temp DECIMAL(5,2),     -- Celsius
    brake_wear_front DECIMAL(5,2),  -- percentage
    brake_wear_rear DECIMAL(5,2),   -- percentage
    parking_brake_engaged BOOLEAN,
    emergency_brake_active BOOLEAN,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_brakes_truck_time ON truck_brakes(truck_id, timestamp DESC);

-- Safety Status
CREATE TABLE IF NOT EXISTS truck_safety_status (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    seatbelt_fastened BOOLEAN,
    operator_id VARCHAR(50),
    operator_logged_in BOOLEAN,
    fatigue_score DECIMAL(5,2),     -- 0-100
    emergency_stop_active BOOLEAN,
    lights_on BOOLEAN,
    beacon_active BOOLEAN,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_truck_safety_truck_time ON truck_safety_status(truck_id, timestamp DESC);

-- ============================================================================
-- PROXIMITY DETECTION TABLES
-- ============================================================================

-- Current proximity status (frequently updated)
CREATE TABLE IF NOT EXISTS truck_proximity_status (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    proximity_system_active BOOLEAN DEFAULT TRUE,
    nearest_vehicle_id VARCHAR(50),
    nearest_vehicle_distance DECIMAL(8,2),  -- meters
    nearest_vehicle_bearing DECIMAL(5,2),   -- degrees
    collision_warning_active BOOLEAN DEFAULT FALSE,
    collision_warning_level VARCHAR(20),    -- info, warning, critical, emergency
    vehicles_in_range TEXT,                 -- JSON array of vehicle IDs
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proximity_status_truck_time ON truck_proximity_status(truck_id, timestamp DESC);

-- Proximity events (historical log)
CREATE TABLE IF NOT EXISTS proximity_events (
    event_id VARCHAR(100) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- Primary vehicle
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    truck_latitude DECIMAL(10,7),
    truck_longitude DECIMAL(10,7),
    truck_speed DECIMAL(6,2),
    truck_heading DECIMAL(5,2),
    
    -- Other vehicle
    other_vehicle_id VARCHAR(50),
    other_vehicle_type VARCHAR(50),  -- truck, light_vehicle, personnel
    other_vehicle_latitude DECIMAL(10,7),
    other_vehicle_longitude DECIMAL(10,7),
    other_vehicle_speed DECIMAL(6,2),
    other_vehicle_heading DECIMAL(5,2),
    
    -- Proximity details
    distance DECIMAL(8,2) NOT NULL,  -- meters
    closing_speed DECIMAL(6,2),      -- m/s
    time_to_collision DECIMAL(8,2),  -- seconds
    
    -- Alert details
    severity VARCHAR(20) NOT NULL,   -- info, warning, critical, emergency
    alert_triggered BOOLEAN DEFAULT FALSE,
    alert_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP,
    
    -- Zone context
    zone_id VARCHAR(50),
    zone_type VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proximity_events_truck_time ON proximity_events(truck_id, timestamp DESC);
CREATE INDEX idx_proximity_events_severity ON proximity_events(severity, timestamp DESC);
CREATE INDEX idx_proximity_events_alert ON proximity_events(alert_triggered, alert_acknowledged);

-- ============================================================================
-- OPERATIONAL TABLES
-- ============================================================================

-- Shift assignments
CREATE TABLE IF NOT EXISTS shifts (
    shift_id VARCHAR(50) PRIMARY KEY,
    site_id VARCHAR(50) REFERENCES sites(site_id),
    shift_name VARCHAR(50),         -- Day, Night, Swing
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operator assignments
CREATE TABLE IF NOT EXISTS operators (
    operator_id VARCHAR(50) PRIMARY KEY,
    employee_number VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    license_class VARCHAR(20),
    site_id VARCHAR(50) REFERENCES sites(site_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Truck-Operator assignment per shift
CREATE TABLE IF NOT EXISTS truck_operator_assignments (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    operator_id VARCHAR(50) REFERENCES operators(operator_id),
    shift_id VARCHAR(50) REFERENCES shifts(shift_id),
    assigned_at TIMESTAMP NOT NULL,
    released_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance records
CREATE TABLE IF NOT EXISTS maintenance_records (
    record_id VARCHAR(100) PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    maintenance_type VARCHAR(50),   -- scheduled, unscheduled, breakdown
    description TEXT,
    engine_hours_at_service DECIMAL(10,2),
    odometer_at_service DECIMAL(12,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    technician_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fault codes
CREATE TABLE IF NOT EXISTS truck_fault_codes (
    id BIGSERIAL PRIMARY KEY,
    truck_id VARCHAR(50) REFERENCES trucks(truck_id),
    fault_code VARCHAR(20) NOT NULL,
    fault_description TEXT,
    severity VARCHAR(20),
    first_detected TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fault_codes_truck_active ON truck_fault_codes(truck_id, is_active);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Current truck status view (latest data for each truck)
CREATE OR REPLACE VIEW v_truck_current_status AS
SELECT 
    t.truck_id,
    t.asset_number,
    tm.model_name,
    t.firmware_version,
    loc.latitude,
    loc.longitude,
    loc.speed,
    loc.heading,
    loc.timestamp as location_timestamp,
    eng.engine_rpm,
    eng.fuel_level,
    eng.engine_temp,
    pay.payload_weight,
    pay.load_status,
    prox.nearest_vehicle_id,
    prox.nearest_vehicle_distance,
    prox.collision_warning_active,
    saf.operator_id,
    saf.seatbelt_fastened
FROM trucks t
LEFT JOIN truck_models tm ON t.model_id = tm.model_id
LEFT JOIN LATERAL (
    SELECT * FROM truck_locations 
    WHERE truck_id = t.truck_id 
    ORDER BY timestamp DESC LIMIT 1
) loc ON true
LEFT JOIN LATERAL (
    SELECT * FROM truck_engine_metrics 
    WHERE truck_id = t.truck_id 
    ORDER BY timestamp DESC LIMIT 1
) eng ON true
LEFT JOIN LATERAL (
    SELECT * FROM truck_payload 
    WHERE truck_id = t.truck_id 
    ORDER BY timestamp DESC LIMIT 1
) pay ON true
LEFT JOIN LATERAL (
    SELECT * FROM truck_proximity_status 
    WHERE truck_id = t.truck_id 
    ORDER BY timestamp DESC LIMIT 1
) prox ON true
LEFT JOIN LATERAL (
    SELECT * FROM truck_safety_status 
    WHERE truck_id = t.truck_id 
    ORDER BY timestamp DESC LIMIT 1
) saf ON true
WHERE t.is_active = TRUE;

-- Active proximity alerts view
CREATE OR REPLACE VIEW v_active_proximity_alerts AS
SELECT 
    pe.*,
    t.asset_number,
    tm.model_name
FROM proximity_events pe
JOIN trucks t ON pe.truck_id = t.truck_id
LEFT JOIN truck_models tm ON t.model_id = tm.model_id
WHERE pe.alert_triggered = TRUE 
  AND pe.alert_acknowledged = FALSE
  AND pe.timestamp > NOW() - INTERVAL '1 hour'
ORDER BY pe.severity DESC, pe.timestamp DESC;

