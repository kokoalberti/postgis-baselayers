ALTER TABLE ONLY geonames.alternatename ADD CONSTRAINT pk_alternatenameid PRIMARY KEY (alternatenameid);
ALTER TABLE ONLY geonames.geoname ADD CONSTRAINT pk_geonameid PRIMARY KEY (geonameid);
ALTER TABLE ONLY geonames.countryinfo ADD CONSTRAINT pk_iso_alpha2 PRIMARY KEY (iso_alpha2);
ALTER TABLE ONLY geonames.countryinfo ADD CONSTRAINT fk_geonameid FOREIGN KEY (geonameid) REFERENCES geonames.geoname(geonameid);
ALTER TABLE ONLY geonames.alternatename ADD CONSTRAINT fk_geonameid FOREIGN KEY (geonameid) REFERENCES geonames.geoname(geonameid);
ALTER TABLE geonames.geoname ADD COLUMN the_geom geometry(Point, 4326);
UPDATE geonames.geoname SET the_geom = ST_PointFromText('POINT(' || longitude || ' ' || latitude || ')', 4326);
CREATE INDEX idx_geoname_the_geom ON geonames.geoname USING gist(the_geom);