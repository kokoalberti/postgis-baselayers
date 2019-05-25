# GADM

The GADM dataset provides administrative spatial data for all countries and their sub-divisions.

## Description

The GADM dataset is available under the `gadm` schema, and consists of tables named `level0` through `level5`  containing global administrative divisions at leveral levels.

## Examples

### Select country that a point falls in

Query:

    SELECT 
         name_0
    FROM 
         gadm.level0
    WHERE 
         ST_Intersects(
            geom, 
            ST_SetSRID(ST_Point(-71.1043443253471, 42.3150676015829), 4326)
         );

Returns:

        name_0     
    ---------------
     United States
    (1 row)

### Return the subdivisions of a particular country

Query:

    SELECT 
        name_1 AS state 
    FROM 
        gadm.level1
    WHERE 
        name_0 = 'United States';

Returns:

            state         
    ----------------------
     Alabama
     Alaska
     Arizona
     Arkansas
     California
     (...)
     West Virginia
     Wisconsin
     Wyoming
    (51 rows)

### Return the countries intersecting a custom geometry

Query:

    SELECT 
        name_0 AS country
    FROM 
        gadm.level0 
    WHERE 
         ST_Intersects(
            level0.geom, 
            ST_SetSRID(ST_GeomFromText('POLYGON((5.22 49.41,6.69 50.12,6.79 49.29,5.22 49.41))'), 4326)
         );

Returns:

      country   
    ------------
     Belgium
     Germany
     France
     Luxembourg
    (4 rows)



## Attribution

[https://gadm.org/](https://gadm.org/)

## License

The data are freely available for academic use and other non-commercial use. Redistribution, or commercial use, is not allowed without prior permission. Using the data to create maps for academic publishing is allowed.