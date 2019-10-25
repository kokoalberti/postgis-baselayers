install: uninstall
	@echo STATUS=Downloading
	mkdir -p src
	cd src && wget -q https://c402277.ssl.cf1.rackcdn.com/publications/17/files/original/GLWD-level2.zip?1343838637 -O GLWD-level2.zip

	psql "$(POSTGRES_URI)" -c 'CREATE SCHEMA IF NOT EXISTS glwd;'
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS glwd.glwd_level_2 CASCADE'

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -skipfailures -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=glwd -lco GEOMETRY_NAME=geom -nln glwd_level_2 /vsizip/src/GLWD-level2.zip/glwd_2.shp

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS glwd.glwd_level_2'
