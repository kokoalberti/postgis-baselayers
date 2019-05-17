all: download install

download:
	@echo Downloading...
	mkdir -p src
	cd src && wget -i ../filelist.txt -c

install:
	@echo Installing dataset...
	mkdir -p tmp

	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS naturalearth CASCADE'
	psql $(POSTGRES_URI) -c 'CREATE SCHEMA naturalearth'

	# Countries as 'ne_10m_admin_0_countries'
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_admin_0_countries /vsizip/src/ne_10m_admin_0_countries.zip/ne_10m_admin_0_countries.shp

	# States and provinces as 'ne_10m_admin_1_states_provinces'
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_admin_1_states_provinces /vsizip/src/ne_10m_admin_1_states_provinces.zip/ne_10m_admin_1_states_provinces.shp

	# Rivers as 'ne_10m_rivers' table. First import the global one as a 
	# new layer using ogr2ogr, then append the europe and north america 
	# supplements
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_lake_centerlines.zip/ne_10m_rivers_lake_centerlines.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_europe.zip/ne_10m_rivers_europe.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_rivers /vsizip/src/ne_10m_rivers_north_america.zip/ne_10m_rivers_north_america.shp

	# Lakes as 'ne_10m_lakes' table. Same as rivers, first import global
	# layer, then append regional supplements.
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes.zip/ne_10m_lakes.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes_europe.zip/ne_10m_lakes_europe.shp
	ogr2ogr -f PostgreSQL -skipfailures -append $(POSTGRES_OGR) -nlt PROMOTE_TO_MULTI -lco SCHEMA=naturalearth -nln ne_10m_lakes /vsizip/src/ne_10m_lakes_north_america.zip/ne_10m_lakes_north_america.shp


	rm -rf tmp
	@echo Done installing!

	#Force an error for dev purposes
	exit 1

clean:
	@echo Cleaning up...
	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS naturalearth CASCADE'
	rm -rf tmp
	rm -rf src

