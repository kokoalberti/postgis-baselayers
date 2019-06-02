install: uninstall
	@echo STATUS=Downloading
	mkdir -p src tmp
	cd src && wget -q https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_admin_0_countries /vsizip/src/ne_10m_admin_0_countries.zip/ne_10m_admin_0_countries.shp

uninstall:
	@echo STATUS=Uninstalling
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS naturalearth.ne_10m_admin_0_countries'

