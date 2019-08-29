install:
	# Copy what we're doing. This shows up in the logs afterwards.
	@echo Installing grand.dams

	# Create the 'src' directory if it doesn't exist yet
	mkdir -p src
	@echo STATUS=Downloading

	# riginal URL which does not support public downloads: https://sedac.ciesin.columbia.edu/downloads/data/grand-v1/grand-v1-dams-rev01/dams-rev01-global-shp.zip
	cd src && wget -q -O dams-rev01-global-shp.zip https://postgis-baselayers-mirrors.s3.eu-central-1.amazonaws.com/grand/dams-rev01-global-shp.zip

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -overwrite $(POSTGRES_OGR) -lco SCHEMA=grand -lco GEOMETRY_NAME=geom -nln dams /vsizip/src/dams-rev01-global-shp.zip/GRanD_dams_v1_1.shp

	# Clean up
	@echo STATUS=Complete

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS grand.dams CASCADE'


