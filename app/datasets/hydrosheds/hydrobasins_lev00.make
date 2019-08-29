install:
	# Copy what we're doing. This shows up in the logs afterwards.
	@echo Installing hydrosheds.hydrobasins

	# Create the 'src' directory if it doesn't exist yet
	#mkdir -p src
	#@echo STATUS=Downloading
	#cd src && wget -q -O hydrobasins_global_lev00.zip https://postgis-baselayers-mirrors.s3.eu-central-1.amazonaws.com/hydrobasins/hydrobasins_global_lev00.zip

	psql "$(POSTGRES_URI)" -c 'CREATE SCHEMA IF NOT EXISTS hydrosheds;'

	# Note! In order for append to work properly the -nln argument needs to include
	# the schema in the name. 

	# Region AF
	@echo STATUS=Importing Region AF [1/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_af_lev00_v1c/hybas_af_lev00_v1c.shp

	# Region AR
	@echo STATUS=Importing Region AR [2/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_ar_lev00_v1c/hybas_ar_lev00_v1c.shp

	# Region AS
	@echo STATUS=Importing Region AS [3/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_as_lev00_v1c/hybas_as_lev00_v1c.shp

	# Region AU
	@echo STATUS=Importing Region AU [4/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_au_lev00_v1c/hybas_au_lev00_v1c.shp

	# Region EU
	@echo STATUS=Importing Region EU [5/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_eu_lev00_v1c/hybas_eu_lev00_v1c.shp

	# Region GR
	@echo STATUS=Importing Region GR [6/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_gr_lev00_v1c/hybas_gr_lev00_v1c.shp

	# Region NA
	@echo STATUS=Importing Region EU [7/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_na_lev00_v1c/hybas_na_lev00_v1c.shp

	# Region SA
	@echo STATUS=Importing Region SA [8/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_sa_lev00_v1c/hybas_sa_lev00_v1c.shp

	# Region SI
	@echo STATUS=Importing Region SI [9/9]
	ogr2ogr -f PostgreSQL -update -append -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=hydrosheds -lco GEOMETRY_NAME=geom -nln hydrosheds.hydrobasins_lev00 /vsizip/hydrobasins_global_lev00.zip/hybas_si_lev00_v1c/hybas_si_lev00_v1c.shp

	# Create indices
	@echo STATUS=Creating Indices
	psql "$(POSTGRES_URI)" -a -f create_indices.sql

	# Clean up
	@echo STATUS=Complete

uninstall:
	@echo STATUS=Uninstalling
	psql "$(POSTGRES_URI)" -c 'DROP TABLE IF EXISTS hydrosheds.hydrobasins_lev00 CASCADE'


