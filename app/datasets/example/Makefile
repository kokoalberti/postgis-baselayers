# ==============================================================================
#
# This Makefile contains the necessary steps to install a dataset into the 
# PostGIS Baselayers application. It's pretty straightforward, but there are a 
# few things to know about how it works.
#
# When 'install' is clicked in the webapp, 'make all' is executed, and when 
# 'uninstall' or 'clean' is clicked, 'make clean' is executed. These make tasks 
# are executed sequentialy in a work queue to avoid overloading the system.
#
# Any task is executed in it's own directory in /opt/postgis-baselayers/<name>/,
# where <name> is the name of the dataset. A task is executed by calling the 
# relevant 'make' command using Python's subprocess module. The command is 
# executed with /opt/postgis-baselayers/<name>/ as the working directory, and
# various convenience environment variables are set as well. Tasks have a 
# timeout of 600 seconds (10 minutes) currently, but this may change later.
#
# When a task is executed, all the files in the dataset's subdirectory in the
# repository (i.e. ~/app/datasets/<name>/) are copied to the /opt/postgis-
# baselayers/<name>/ directory, before the 'make' command is issued. This 
# allows for additional helper files (filelist.txt being a common one) to be 
# included.
#
# ==============================================================================
# The 'all' target just downloads and installs the dataset. 
all: download install

# ==============================================================================
# The 'download' target downloads the data required for this dataset. The 'src'
# subdirectory is used for the downloading.
download:
	# Copy what we're doing. This shows up in the logs afterwards.
	@echo Downloading...

	# Create the 'src' directory if it doesn't exist yet
	mkdir -p src

	# Change to the 'src' directory and use wget to download the files. 
	#
	# The -i flag lets you specify a list of files to download, for which we 
	# use the filelist.txt file.
	#
	# The -c flag is used to 'continue' a download. This is useful for when a
	# download fails, we can just run the same command again and it will keep
	# going where it left off. Additionally, if the source data has been 
	# downloaded once already, we will not have to download it again if the 
	# install script is run again. In case we want to really start all over 
	# again, the 'make clean' can be run.
	#
	# In this example the filelist.txt contains only one file, which can be 
	# found at: http://ourairports.com/data/airports.csv
	cd src && wget -i ../filelist.txt -c

# ==============================================================================
# The 'install' target is responsible for installing the downloaded dataset 
# into the PostGIS database in a sensible manner. Exactly how this is done is 
# left up to the implementor to decide. There are a few things to keep in mind:
#
# - Use a schema with the same name as the dataset, in this case 'example'
#
# - Try to make the appropriate geometry colums in the database
#
# - Add the appropriate indices on geometry columns, but also on other columns
#   which may be used in selections.
#
# Because the make script is run from Python using the subprocess module, 
# several environment variables will have been set that may be helpful in 
# processing the data and making it ready to insert info the database. In 
# addition to the environment variables defined in the '.env' file, the
# following are also set:
#
# POSTGRES_URI - A postgres connection URI filled with the correct username,
# password, database, etc. for the database to which the web appliation is 
# connected. This lets you run SQL commands on the database easily using the 
# psql command like application as follows:
#
#    psql $(POSTGRES_URI) -c 'CREATE SCHEMA example'
#
# Or to run commands from a specific file:
#
#    psql $(POSTGRES_URI) -a -f sql_commands_to_execute.sql
#
# POSTGRES_OGR - A filled in postgres connection string for use with GDAL/OGR,
# allowing you to run commands like:
#
#    ogr2ogr -f PostgreSQL -overwrite -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) \
#            -lco SCHEMA=example_schema -nln example_table tmp/example.shp
#
# Which will then load the example.shp file into example_table in the example
# schema using the ogr2ogr tool.
#
install:
	# Copy what we're doing
	@echo Installing dataset...

	# Create the tmp directory in which we'll do our processing
	mkdir -p tmp

	# We need to import the file downloaded in the download step, which is a 
	# CSV file 'airports.csv' with the first line containing the column names.
	#
	# Our approach to installing this file in the 'example' schema will be with
	# the following steps:
	#
	# 1. Create the 'example' schema in the database
	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS example CASCADE'
	psql $(POSTGRES_URI) -c 'CREATE SCHEMA example'

	# 2. Create an empty table based with the 'create_tables.sql' file which
	#    has been made as part of this dataset. It would probably be possible
	#    to use ogr2ogr to do this automatically, but this way we have more
	#    control over what the table and column data types look like.
	psql $(POSTGRES_URI) -a -f create_tables.sql

	# 3. Import the data from the CSV into the table. We pipe the csv into
	#    the psql command, adding some options to ignore the first row and 
	#    specifying that our file uses a ',' delimiter.
	cat src/airports.csv | psql $(POSTGRES_URI) -c "COPY airports (id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords) FROM stdin WITH DELIMITER ',' CSV HEADER"

	# 4. We now have the data in a table, but there is no geometry field yet
	#    and no indices on the geometry or on other columns. We add those using
	#    the create_indices.sql file.
	psql $(POSTGRES_URI) -a -f create_indices.sql

	# Clean up
	rm -rf tmp
	@echo Done installing!

# ==============================================================================
# The 'clean' target is responsible for cleaning up or uninstalling a dataset
# completely. It should do the following things:
#
# - Remove the schema from the database, using the CASCADE option to also 
#   delete all tables in the schema.
#
# - Remove the tmp and src directories that may contain partial or complete 
#   downloads, or intermediary products used in the installation of the 
#   dataset.
clean:
	@echo Cleaning up...
	psql $(POSTGRES_URI) -c 'DROP SCHEMA IF EXISTS example CASCADE'
	rm -rf tmp
	rm -rf src

