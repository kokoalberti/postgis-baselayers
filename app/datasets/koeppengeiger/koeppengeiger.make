
install: uninstall
	@echo "Installing koeppengeiger.koeppengeiger..."
	mkdir -p src tmp
	cd src && wget -q -i ../filelist.txt

	# Observed 1976-2000
	unzip -o src/1976-2000_GIS.zip -d tmp 
	ogr2ogr tmp/period_1976_2000.shp tmp/1976-2000.shp 
	ogr2ogr -t_srs 'EPSG:4326' -f PostgreSQL -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=koeppengeiger -nln koeppengeiger -sql "SELECT 'obs_1976_2000' AS scenario, '' AS classification, GRIDCODE AS gridcode FROM period_1976_2000" tmp/period_1976_2000.shp

	# Observed 1951-1975
	#unzip -o src/1951-1975_GIS.zip -d tmp
	#ogr2ogr tmp/period_1951_1975.shp tmp/1951-1975.shp
	#ogr2ogr -t_srs 'EPSG:4326' -f PostgreSQL -nlt PROMOTE_TO_MULTI $(POSTGRES_OGR) -lco SCHEMA=koeppengeiger -nln koeppengeiger -sql "SELECT 'obs_1951_1975' AS scenario, '' AS classification, GRIDCODE AS gridcode FROM period_1951_1975" tmp/period_1951_1975.shp

	# Add the legend to the table
	cp src/legend.txt tmp/legend.txt
	sed -i 's/ ... /,/g' tmp/legend.txt
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS koeppengeiger.koeppengeiger_classes'
	psql $(POSTGRES_URI) -c 'CREATE TABLE koeppengeiger.koeppengeiger_classes (gridcode int, classification varchar)'
	cat tmp/legend.txt | psql $(POSTGRES_URI) -c "COPY koeppengeiger.koeppengeiger_classes (gridcode,classification) from stdin with delimiter E',' null as ''"
	psql $(POSTGRES_URI) -c 'UPDATE koeppengeiger.koeppengeiger SET classification = koeppengeiger_classes.classification FROM koeppengeiger.koeppengeiger_classes WHERE koeppengeiger.gridcode = koeppengeiger_classes.gridcode'
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS koeppengeiger_classes'

uninstall:
	@echo "Uninstalling koeppengeiger.koeppengeiger"
	psql $(POSTGRES_URI) -c 'DROP TABLE IF EXISTS koeppengeiger.koeppengeiger'



