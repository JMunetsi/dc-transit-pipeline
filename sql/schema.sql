-- Warehouse schema for cleaned WMATA bus position data.
-- Works as-is for SQLite; adjust types slightly for BigQuery
-- (TIMESTAMP instead of TEXT, FLOAT64 instead of REAL).

CREATE TABLE IF NOT EXISTS bus_positions (
    VehicleID   TEXT,
    RouteID     TEXT,
    Lat         REAL,
    Lon         REAL,
    DateTime    TEXT,
    Direction   TEXT,
    TripID      TEXT
);

CREATE INDEX IF NOT EXISTS idx_bus_positions_datetime
    ON bus_positions (DateTime);

CREATE INDEX IF NOT EXISTS idx_bus_positions_route
    ON bus_positions (RouteID);
