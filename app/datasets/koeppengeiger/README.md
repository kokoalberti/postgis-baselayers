# Köppen-Geiger Climate Classification

The `koeppengeiger` dataset contains global data of historic and present climate classifications according to the Köppen-Geiger climate classification scheme.

## Description

The data is stored in the `koeppengeiger` schema, in a table called `koeppengeiger`. The `wkb_geometry` column contains the geometry, the `scenario` column contains the scenario, and the `classification` contains the climate classification code.

## Examples

### Obtain climate classification of a point location

Use the following query to obtain the climate classification under different scenarios:

    SELECT 
         scenario, classification
    FROM 
         koeppengeiger.koeppengeiger 
    WHERE 
         ST_Intersects(
            koeppengeiger.wkb_geometry, 
            ST_SetSRID(ST_Point(-71.1043443253471, 42.3150676015829), 4326)
         );

Which returns:

       scenario    | classification 
    ---------------+----------------
     obs_1951_1975 | Cfa
     obs_1976_2000 | Dfa
    (2 rows)


## Attribution

Kottek, M., J. Grieser, C. Beck, B. Rudolf, and F. Rubel, 2006: World Map of the Köppen-Geiger climate classification updated. Meteorol. Z., 15, 259-263. DOI: 10.1127/0941-2948/2006/0130.

More information about this dataset can be found via the [Köppen-Geiger Climate Classification](http://koeppen-geiger.vu-wien.ac.at/present.htm) page at the VU Wien.

## License

Unknown.
