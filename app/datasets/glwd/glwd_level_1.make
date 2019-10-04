install: uninstall
	@echo STATUS=Downloading
	mkdir -p src
	cd src && wget -q https://c402277.ssl.cf1.rackcdn.com/publications/16/files/original/GLWD-level1.zip?1343838522 -O GLWD-level1.zip

	psql "$(POSTGRES_URI)" -c 'CREATE SCHEMA IF NOT EXISTS glwd;'
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS glwd.glwd_level_1 CASCADE'

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=glwd -lco GEOMETRY_NAME=wkb_geometry -nln glwd_level_1 /vsizip/src/GLWD-level1.zip/glwd_1.shp

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS glwd.glwd_level_1'
