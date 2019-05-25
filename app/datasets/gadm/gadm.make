install: uninstall
	@echo STATUS=Downloading
	mkdir -p src tmp
	cd src && wget -q https://biogeo.ucdavis.edu/data/gadm3.6/gadm36_levels_gpkg.zip

	@echo STATUS=Importing
	unzip -o src/gadm36_levels_gpkg.zip -d tmp
	ogr2ogr -f PostgreSQL -overwrite $(POSTGRES_OGR) -lco SCHEMA=gadm tmp/gadm36_levels.gpkg

uninstall:
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level0'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level1'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level2'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level3'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level4'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS gadm.level5'

