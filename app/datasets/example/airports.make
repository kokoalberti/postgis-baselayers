install:
	# Copy what we're doing. This shows up in the logs afterwards.
	@echo Installing example.airports

	# Create the 'src' directory if it doesn't exist yet
	mkdir -p src
	@echo STATUS=Downloading
	cd src && wget -q http://ourairports.com/data/airports.csv

	@echo STATUS=Importing
	psql $(POSTGRES_URI) -a -f create_tables.sql
	cat src/airports.csv | psql $(POSTGRES_URI) -c "COPY example.airports (id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords) FROM stdin WITH DELIMITER ',' CSV HEADER"
	psql $(POSTGRES_URI) -a -f create_indices.sql

	# Clean up
	@echo STATUS=Complete

uninstall:
	@echo Uninstalling example.airports
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS example.airports CASCADE'


