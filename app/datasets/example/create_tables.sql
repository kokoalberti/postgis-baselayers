DROP TABLE IF EXISTS example.airports;
CREATE TABLE example.airports (
    id integer,
    ident varchar(256),
    type varchar(256),
    name varchar(256),
    latitude_deg float,
    longitude_deg float,
    elevation_ft integer,
    continent varchar(2),
    iso_country varchar(2),
    iso_region varchar(12),
    municipality varchar(256),
    scheduled_service varchar(12),
    gps_code varchar(4),
    iata_code varchar(4),
    local_code varchar(12),
    home_link varchar(256),
    wikipedia_link varchar(256),
    keywords varchar(256)
 );
