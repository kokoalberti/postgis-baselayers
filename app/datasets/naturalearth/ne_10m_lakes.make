install: uninstall
	@echo STATUS=Downloading
	mkdir -p src
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_lakes.zip
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_lakes_north_america.zip
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_lakes_europe.zip

	@echo STATUS=Importing
	# Lakes as 'ne_10m_lakes' table. Same as rivers, first import global
	# layer, then append regional supplements.
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes.zip/ne_10m_lakes.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes_europe.zip/ne_10m_lakes_europe.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes_north_america.zip/ne_10m_lakes_north_america.shp

uninstall:
	@echo STATUS=Uninstalling
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS naturalearth.ne_10m_lakes'

