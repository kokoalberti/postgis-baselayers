all: download install

download:
	@echo Downloading...
	mkdir -p src
	cd src && wget -i ../filelist.txt -c

install:
	@echo Installing dataset...
	mkdir -p tmp

	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS geonames CASCADE'
	psql $(POSTGRES_URI) -c 'CREATE SCHEMA geonames'

	# Unzip source file
	unzip -o src/allCountries.zip -d tmp
	unzip -o src/alternateNames.zip -d tmp

	# Remove comments from countryInfo.txt
	# TODO: remove lines starting with # instead of this. 
	tail +52 src/countryInfo.txt > tmp/countryInfo.txt

	# Create the geonames tables
	psql $(POSTGRES_URI) -a -f geonames_create_tables.sql

	# Import data
	cat tmp/allCountries.txt | psql $(POSTGRES_URI) -c "COPY geoname (geonameid,name,asciiname,alternatenames,latitude,longitude,fclass,fcode,country,cc2,admin1,admin2,admin3,admin4,population,elevation,gtopo30,timezone,moddate) FROM stdin null as ''"
	cat tmp/alternateNames.txt | psql $(POSTGRES_URI) -c "COPY alternatename (alternatenameid,geonameid,isolanguage,alternatename,ispreferredname,isshortname,iscolloquial,ishistoric) from stdin null as ''"
	cat tmp/countryInfo.txt | psql $(POSTGRES_URI) -c "COPY countryinfo (iso_alpha2,iso_alpha3,iso_numeric,fips_code,name,capital,areainsqkm,population,continent,tld,currencycode,currencyname,phone,postalcode,postalcoderegex,languages,geonameid,neighbors,equivfipscode) from stdin with delimiter E'\t' null as ''"

	# Create geometries and indices
	psql $(POSTGRES_URI) -a -f geonames_create_indices.sql

	# Clean up
	rm -rf tmp

clean:
	@echo Cleaning up...
	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS geonames CASCADE'
	rm -rf tmp
	rm -rf src

