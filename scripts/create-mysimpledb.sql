-- ============================================================
-- T-SQL Script to create mysimpledb database
-- Run with: sqlcmd -S <server> -U <username> -P <password> -i create-mysimpledb.sql
-- ============================================================

-- ============================================================
-- Create admin user: debezium (for CDC/Debezium connector)
-- ============================================================

-- Create login at server level (run as SA or admin)
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'debezium')
BEGIN
    CREATE LOGIN debezium WITH PASSWORD = 'debezium';
    PRINT 'Login debezium created successfully.';
END
ELSE
BEGIN
    PRINT 'Login debezium already exists.';
END
GO

-- Grant server-level permissions for CDC
ALTER SERVER ROLE sysadmin ADD MEMBER debezium;
PRINT 'Granted sysadmin role to debezium.';
GO

-- ============================================================
-- Create the database
-- ============================================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'mysimpledb')
BEGIN
    CREATE DATABASE mysimpledb;
    PRINT 'Database mysimpledb created successfully.';
END
ELSE
BEGIN
    PRINT 'Database mysimpledb already exists.';
END
GO

-- Switch to the new database
USE mysimpledb;
GO

-- Create database user for debezium login
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'debezium')
BEGIN
    CREATE USER debezium FOR LOGIN debezium;
    PRINT 'Database user debezium created successfully.';
END
ELSE
BEGIN
    PRINT 'Database user debezium already exists.';
END
GO

-- Grant db_owner role to debezium user
ALTER ROLE db_owner ADD MEMBER debezium;
PRINT 'Granted db_owner role to debezium.';
GO

-- Enable CDC on the database (required for Debezium)
EXEC sys.sp_cdc_enable_db;
PRINT 'CDC enabled on mysimpledb database.';
GO

-- Create the truck_locations table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'truck_locations')
BEGIN
    CREATE TABLE truck_locations (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        truck_id        INT NOT NULL,
        time            DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        latitude        DECIMAL(10, 7) NOT NULL,
        longitude       DECIMAL(10, 7) NOT NULL
    );
    
    -- Create index on truck_id for faster queries
    CREATE INDEX idx_truck_id ON truck_locations(truck_id);
    
    -- Create index on time for time-based queries
    CREATE INDEX idx_time ON truck_locations(time);
    
    PRINT 'Table truck_locations created successfully.';
    
    -- Enable CDC on the truck_locations table (for Debezium)
    EXEC sys.sp_cdc_enable_table
        @source_schema = 'dbo',
        @source_name = 'truck_locations',
        @role_name = NULL,
        @supports_net_changes = 1;
    PRINT 'CDC enabled on truck_locations table.';
END
ELSE
BEGIN
    PRINT 'Table truck_locations already exists.';
END
GO

-- Insert some sample data
INSERT INTO truck_locations (truck_id, time, latitude, longitude)
VALUES 
    (1, GETUTCDATE(), -23.3601, 119.7310),
    (2, GETUTCDATE(), -23.3615, 119.7325),
    (3, GETUTCDATE(), -23.3680, 119.7290),
    (4, GETUTCDATE(), -23.3695, 119.7305),
    (5, GETUTCDATE(), -23.3520, 119.7450),
    (6, GETUTCDATE(), -23.3535, 119.7465),
    (7, GETUTCDATE(), -23.3400, 119.7600),
    (8, GETUTCDATE(), -23.3415, 119.7615),
    (9, GETUTCDATE(), -23.3750, 119.7200),
    (10, GETUTCDATE(), -23.3765, 119.7215);

PRINT 'Sample data inserted successfully.';
GO

-- Verify the table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'truck_locations';
GO

-- Show sample data
SELECT * FROM truck_locations;
GO

PRINT 'Database setup complete!';
GO

