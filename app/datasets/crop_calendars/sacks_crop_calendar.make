install:
	# Copy what we're doing. This shows up in the logs afterwards.
	@echo Installing crop calendars

	# Create the 'src' directory if it doesn't exist yet
	mkdir -p src
	@echo STATUS=Downloading

	# Original URLs are down. Use mirror.
	cd src && wget -q -O sacks_crop_calendar.gpkg https://postgis-baselayers-mirrors.s3.eu-central-1.amazonaws.com/sacks_crop_calendar/sacks_crop_calendar.gpkg

	@echo STATUS=Importing
	ogr2ogr -f PostgreSQL -overwrite $(POSTGRES_OGR) -lco SCHEMA=crop_calendars -lco GEOMETRY_NAME=geom -nln sacks_crop_calendar src/sacks_crop_calendar.gpkg

	# Clean up
	@echo STATUS=Complete

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS crop_calendars.sacks_crop_calendar CASCADE'


