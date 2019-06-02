install: uninstall
	@echo STATUS=Downloading
	mkdir -p src tmp
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_populated_places.zip

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -skipfailures -overwrite $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_populated_places /vsizip/src/ne_10m_populated_places.zip/ne_10m_populated_places.shp

uninstall:
	@echo STATUS=Uninstalling
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS naturalearth.ne_10m_populated_places'

