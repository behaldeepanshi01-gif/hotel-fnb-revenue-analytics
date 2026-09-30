-- Hotel F&B Revenue Analytics: schema (SQLite / works in most SQL engines)
-- rooms_daily = REAL occupancy rebuilt from public bookings
-- fnb_daily   = SIMULATED F&B, driven by the real in-house guest counts

DROP TABLE IF EXISTS rooms_daily;
CREATE TABLE rooms_daily (
    date                  DATE PRIMARY KEY,
    occupied_rooms        INTEGER,
    in_house_guests       INTEGER,
    room_revenue          REAL,
    breakfast_pkg_guests  INTEGER,   -- guests whose rate includes breakfast (BB/HB/FB)
    dinner_pkg_guests     INTEGER,   -- guests whose rate includes dinner (HB/FB)
    rooms_available       INTEGER,   -- estimated: busiest night observed
    occupancy_pct         REAL,
    fiscal_year           TEXT
);

DROP TABLE IF EXISTS fnb_daily;
CREATE TABLE fnb_daily (
    date                DATE,
    outlet              TEXT,
    daypart             TEXT,
    hotel_guest_covers  INTEGER,
    outside_covers      INTEGER,
    covers              INTEGER,
    revenue             REAL
);

DROP TABLE IF EXISTS dim_outlet;
CREATE TABLE dim_outlet (
    outlet       TEXT PRIMARY KEY,
    outlet_type  TEXT,
    seats        INTEGER
);
