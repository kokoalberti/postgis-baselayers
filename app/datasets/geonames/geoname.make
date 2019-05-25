all: download install

install: uninstall
	@echo Installing dataset...
	mkdir -p src tmp
	cd src && wget -q -i ../filelist.txt

	# Unzip source file
	unzip -o src/allCountries.zip -d tmp
	unzip -o src/alternateNames.zip -d tmp

	# Remove comments from countryInfo.txt
	# TODO: remove lines starting with # instead of this. 
	tail +52 src/countryInfo.txt > tmp/countryInfo.txt

	# Create the geonames tables
	psql $(POSTGRES_URI) -a -f geoname_create_tables.sql

	# Import data
	cat tmp/allCountries.txt | psql $(POSTGRES_URI) -c "COPY geonames.geoname (geonameid,name,asciiname,alternatenames,latitude,longitude,fclass,fcode,country,cc2,admin1,admin2,admin3,admin4,population,elevation,gtopo30,timezone,moddate) FROM stdin null as ''"
	cat tmp/alternateNames.txt | psql $(POSTGRES_URI) -c "COPY geonames.alternatename (alternatenameid,geonameid,isolanguage,alternatename,ispreferredname,isshortname,iscolloquial,ishistoric) from stdin null as ''"
	cat tmp/countryInfo.txt | psql $(POSTGRES_URI) -c "COPY geonames.countryinfo (iso_alpha2,iso_alpha3,iso_numeric,fips_code,name,capital,areainsqkm,population,continent,tld,currencycode,currencyname,phone,postalcode,postalcoderegex,languages,geonameid,neighbors,equivfipscode) from stdin with delimiter E'\t' null as ''"

	# Create geometries and indices
	psql $(POSTGRES_URI) -a -f geoname_create_indices.sql

	# Clean up
	rm -rf tmp

uninstall:
	@echo Uninstalling
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS geonames.geoname CASCADE'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS geonames.alternatename CASCADE'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS geonames.countryinfo CASCADE'


