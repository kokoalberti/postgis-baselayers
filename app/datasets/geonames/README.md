# Geonames

The Geonames geographical database covers all countries and contains over eleven million placenames.

## Description

The Geonames database is available under the `geonames` schema, and consists of the `alternatename`, `countryinfo`, and `geoname` tables. 

The `geoname` table contains the main collection of features. Each feature has a geometry column called `the_geom`, and a feature class and code in the `fclass` and `fcode` column to specify what type of feature it is. A detailed list of all the available [geonames feature classes](http://www.geonames.org/export/codes.html) is on the Geonames website. The feature class is a useful attribute to filter and restrict your results to the type of things that you're interested in.

For more information on the contents of the tables see the [readme](http://download.geonames.org/export/dump/readme.txt).

## Examples

### Find populated places within a polygon, sorted by population

Query:

    SELECT 
        name, 
        asciiname, 
        population,
        country
    FROM 
        geonames.geoname 
    WHERE 
        (
            fcode = 'PPL' OR 
            fcode = 'PPLA' OR 
            fcode = 'PPLA2' OR 
            fcode = 'PPLA3' OR 
            fcode = 'PPLC' OR 
            fcode = 'PPLG'
        ) 
        AND
            ST_Intersects(
                the_geom, 
                ST_SetSRID(ST_GeomFromText('POLYGON((-8.10 38.86,-4.47 39.29,-5.96 36.87,-8.10 38.86))'), 4326)
            ) 
    ORDER BY 
        population DESC
    LIMIT 10;

Returns:

                name            |         asciiname          | population | country 
    ----------------------------+----------------------------+------------+---------
     Sevilla                    | Sevilla                    |     703206 | ES
     Badajoz                    | Badajoz                    |     148334 | ES
     Dos Hermanas               | Dos Hermanas               |     122943 | ES
     Alcalá de Guadaira         | Alcala de Guadaira         |      70155 | ES
     Mérida                     | Merida                     |      56395 | ES
     Utrera                     | Utrera                     |      50665 | ES
     Mairena del Aljarafe       | Mairena del Aljarafe       |      40700 | ES
     Los Palacios y Villafranca | Los Palacios y Villafranca |      36824 | ES
     La Rinconada               | La Rinconada               |      35928 | ES
     Don Benito                 | Don Benito                 |      35791 | ES
    (10 rows)

### Find the highest capital cities in the world

Query:

    SELECT 
        name, 
        gtopo30 AS elevation
    FROM 
        geonames.geoname 
    WHERE 
        fcode = 'PPLC' 
    ORDER BY 
        elevation DESC
    LIMIT 10;

Returns:

        name     | elevation 
    -------------+-----------
     Quito       |      2854
     Sucre       |      2798
     Bogotá      |      2582
     Addis Ababa |      2405
     Asmara      |      2334
     Thimphu     |      2307
     Sanaa       |      2253
     Mexico City |      2240
     Gitega      |      1849
     Kabul       |      1798
    (10 rows)

### List of volcanos in Italy

Query:

    SELECT 
        name, 
        gtopo30 AS elevation
    FROM 
        geonames.geoname 
    WHERE 
        fcode = 'VLC' AND
        country = 'IT' 
    ORDER BY 
        elevation DESC
    LIMIT 10;

Returns:

         name      | elevation 
    ---------------+-----------
     Monte Etna    |      3291
     Vesuvius      |      1240
     Stromboli     |       841
     Monte Epomeo  |       757
     Roccamonfina  |       602
     Camaldoli     |       456
     Gran Cratere  |       363
     La Solfatara  |        95
     Monte Barbaro |        70
     Agnano        |        63
    (10 rows)

## Attribution

See the downloads section [https://www.geonames.org/about.html](https://www.geonames.org/about.html) for more information.

## License

Creative Commons Attribution 4.0