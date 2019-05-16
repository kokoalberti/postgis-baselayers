all: clean download install

download:
	@echo Downloading...
	mkdir -p src
	cd src && wget -i ../filelist.txt -c

install:
	@echo Installing dataset...
	mkdir -p tmp

	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS gadm CASCADE'
	psql $(POSTGRES_URI) -c 'CREATE SCHEMA gadm'

	# GADM Level 0
	unzip -o src/gadm36_0.zip -d tmp
	ogr2ogr -f PostgreSQL -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=gadm -nln gadm_0 tmp/gadm36_0.shp

	# GADM Level 1
	unzip -o src/gadm36_1.zip -d tmp
	ogr2ogr -f PostgreSQL -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=gadm -nln gadm_1 tmp/gadm36_1.shp

	# GADM Level 2
	unzip -o src/gadm36_2.zip -d tmp
	ogr2ogr -f PostgreSQL -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=gadm -nln gadm_2 tmp/gadm36_2.shp

	# Clean up
	rm -rf tmp

clean:
	@echo Cleaning up...
	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS gadm CASCADE'
	rm -rf tmp
	rm -rf src

