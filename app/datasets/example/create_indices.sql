-- Create primary key
ALTER TABLE ONLY airports ADD CONSTRAINT pk_id PRIMARY KEY (id);

-- Add a geometry column called 'geom' of type Point
ALTER TABLE airports ADD COLUMN geom geometry(Point, 4326);

-- Fill the geometry column with a point created from the longitude_dev and latitude_deg columns
UPDATE airports SET geom = ST_PointFromText('POINT(' || longitude_deg || ' ' || latitude_deg || ')', 4326);

-- Creata a spatial index on the geom column
CREATE INDEX idx_airports_geom ON airports USING gist(geom);

-- Create some other indices on the name and type columns
CREATE INDEX idx_airports_name ON airports (name);
CREATE INDEX idx_airports_type ON airports (type);
CREATE INDEX idx_airports_name_type ON airports (type, name);