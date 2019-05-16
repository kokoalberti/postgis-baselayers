ALTER TABLE ONLY alternatename ADD CONSTRAINT pk_alternatenameid PRIMARY KEY (alternatenameid);
ALTER TABLE ONLY geoname ADD CONSTRAINT pk_geonameid PRIMARY KEY (geonameid);
ALTER TABLE ONLY countryinfo ADD CONSTRAINT pk_iso_alpha2 PRIMARY KEY (iso_alpha2);
ALTER TABLE ONLY countryinfo ADD CONSTRAINT fk_geonameid FOREIGN KEY (geonameid) REFERENCES geoname(geonameid);
ALTER TABLE ONLY alternatename ADD CONSTRAINT fk_geonameid FOREIGN KEY (geonameid) REFERENCES geoname(geonameid);
ALTER TABLE geoname ADD COLUMN the_geom geometry(Point, 4326);
UPDATE geoname SET the_geom = ST_PointFromText('POINT(' || longitude || ' ' || latitude || ')', 4326);
CREATE INDEX idx_geoname_the_geom ON geoname USING gist(the_geom);