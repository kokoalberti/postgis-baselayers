install: uninstall
	@echo STATUS=Downloading
	mkdir -p src
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_rivers_lake_centerlines.zip
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_rivers_north_america.zip
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_rivers_europe.zip
		
	@echo STATUS=Importing
	# Rivers as 'ne_10m_rivers' table. First import the global one as a 
	# new layer using ogr2ogr, then append the europe and north america 
	# supplements
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -lco GEOMETRY_NAME=geom -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_lake_centerlines.zip/ne_10m_rivers_lake_centerlines.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -lco GEOMETRY_NAME=geom -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_europe.zip/ne_10m_rivers_europe.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -lco GEOMETRY_NAME=geom -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_north_america.zip/ne_10m_rivers_north_america.shp

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS naturalearth.ne_10m_rivers'

