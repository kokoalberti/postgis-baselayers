# Natural Earth

Natural Earth is a public domain map dataset available at 1:10m, 1:50m, and 1:110 million scales. 

## Description

Because the Natural Earth dataset is quite extensive, only a selection of the layers from the 1:10m version are currently available in PostGIS Baselayers. The dataset uses the `naturalearth` schema in the database, with the tables described below.

### ne_10m_admin_0_countries

Simple layer of countries at the Admin 0 level. Column `wkb_geometry` contains the geometry, and `name` the common name of the country. Also includes various other data fields such as population, abbreviations, GDP estimates, and names in various other languages. 

More information: [https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/)

### ne_10m_admin_1_states_provinces

Contains level 1 adminitrative subdivisions such as states and provinces. Column `wkb_geometry` contains the geometry and `name` contains the name of the division. Various other fields are also available.

More information: [https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)

### ne_10m_populated_places

Contains point locations of populated places. Column `wkb_geometry` contains the geometry, and `name` contains the name of the place. Various other fields also included.

More information: [https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/)

### ne_10m_lakes

Contains global lakes and reservoirs, including the Europe and North America supplements. Column `wkb_geometry` contains the geometry, `featurecla` is a feature class to differentiate between lakes and reservoirs, and `name` contains the name of the feature.

More information: [https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-lakes/](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-lakes/)

### ne_10m_rivers

Contains global rivers and lakes centerlines, including the Europe and North America supplements. Column `wkb_geometry` contains the geometry, and `name` contains the common name of the feature.

More information: [https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/)

## Examples

### Make a list of rivers in Poland

Query:

    SELECT 
        DISTINCT ne_10m_rivers.name
    FROM 
        naturalearth.ne_10m_admin_0_countries, 
        naturalearth.ne_10m_rivers 
    WHERE 
        ne_10m_admin_0_countries.name = 'Poland' AND 
		ne_10m_rivers.name != '' AND
        ST_Intersects(
            ne_10m_admin_0_countries.wkb_geometry,
            ne_10m_rivers.wkb_geometry
        ) 
    ORDER BY 
        name

Returns:

         name     
    --------------
     Bóbr
     Bug
     Bzura
     Drwęca
     Dunajec
     (...)
     Vistula
     Warta
     Wieprz
     Wkra
    (23 rows)

### Find the largest reservoirs in the State of California

Query:

    SELECT 
        ne_10m_lakes.name,
        ST_Area(ne_10m_lakes.wkb_geometry::geography)/(1000*1000) AS area_sq_km
    FROM 
        naturalearth.ne_10m_admin_1_states_provinces, 
        naturalearth.ne_10m_lakes 
    WHERE 
        ne_10m_admin_1_states_provinces.name = 'California' AND 
        ne_10m_lakes.featurecla = 'Reservoir' AND
        ST_Intersects(
            ne_10m_admin_1_states_provinces.wkb_geometry,
            ne_10m_lakes.wkb_geometry
        ) 
    ORDER BY 
        area_sq_km DESC

Result:

             name         |    area_sq_km    
    ----------------------+------------------
     Shasta Lake          | 135.087412145496
     Lake Oroville        | 107.874048788475
     Trinity Lake         | 99.3003356783872
     Clear Lake Reservoir | 89.9109302558184
     San Luis Reservoir   | 72.7709784402466
     Millerton Lake       |  21.868824642725
    (6 rows)

### Find capital cities in Europe with a river running through it

Query:

	SELECT 
		ne_10m_populated_places.name AS city_name,
		ne_10m_rivers.name_en AS river_name
	FROM 
		naturalearth.ne_10m_populated_places,
		naturalearth.ne_10m_rivers
	WHERE 
		ne_10m_populated_places.adm0cap = 1 AND 
		ne_10m_rivers.name_en != '' AND
		ST_Within(
			ne_10m_populated_places.wkb_geometry,
			(SELECT ST_Union(wkb_geometry) FROM naturalearth.ne_10m_admin_0_countries WHERE continent='Europe')
		) AND
		ST_Intersects(ST_Buffer(ne_10m_populated_places.wkb_geometry, 0.05), ne_10m_rivers.wkb_geometry)
	ORDER BY 
	 	ne_10m_populated_places.pop_max DESC
	LIMIT 10;

Result:

     city_name |       river_name        
    -----------+-------------------------
     Paris     | Seine
     London    | Thames
     Berlin    | Spree
     Rome      | Tiber
     Kiev      | Desna
     Kiev      | Dnieper
     Warsaw    | Vistula
     Budapest  | Ráckeve-Soroksár Danube
     Budapest  | Danube
     Stockholm | Arboga
    (10 rows)


## Attribution

See [https://www.naturalearthdata.com/about/](https://www.naturalearthdata.com/about/) for more information.

## Licensing

Natural Earth data is in the public domain. See [https://www.naturalearthdata.com/about/terms-of-use/](https://www.naturalearthdata.com/about/terms-of-use/) for more information.

