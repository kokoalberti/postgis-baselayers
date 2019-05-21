# Accessing data with PSQL

Connect to the database using psql as `psql postgresql://postgis:postgis@localhost:35432/postgis-database`.

Once connected the rest should be straightforward:

    $ psql postgresql://postgis:postgis@localhost:35432/postgis-database
    psql (11.3 (Ubuntu 11.3-1.pgdg18.04+1), server 10.5 (Debian 10.5-1.pgdg90+1))
    Type "help" for help.

    postgis-database=# \dn
           List of schemas
            Name        |  Owner  
    --------------------+---------
     gadm               | postgis
     geonames           | postgis
     koeppengeiger      | postgis
     naturalearth       | postgis
     postgis_baselayers | postgis
     public             | postgis
     tiger              | postgis
     tiger_data         | postgis
     topology           | postgis
    (9 rows)

    postgis-database=# SELECT name, gtopo30 AS elevation FROM geonames.geoname WHERE fcode = 'PPLC' ORDER BY elevation DESC LIMIT 10;
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

    postgis-database=#
