# Example Dataset

This is an example dataset that is well documented and serves as a simple example of how to add other datasets to the PostGIS Baselayers application.

## Description

The example dataset is a simple dataset of airport locations available from [http://ourairports.com/data/](http://ourairports.com/data/). The files that need to be downloaded are `http://ourairports.com/data/airports.csv`, and this file has been added to the `filelist.txt` file in the `example` dataset.

Refer to the `Makefile` in the `datasets/example/` directory for more information about how datasets are downloaded and imported into the PostGIS Baselayers application.

## Examples

### Find large airports within 100km of Central London

Query:

    SELECT 
        name 
    FROM 
        example.airports 
    WHERE 
        type = 'large_airport' AND 
        ST_DWithin(geom, ST_SetSRID(ST_Point(-0.13, 51.49), 4326)::geography, 100000);

Result:

              name           
    -------------------------
     London Luton Airport
     London Gatwick Airport
     London Heathrow Airport
     London Stansted Airport
    (4 rows)



## Attributiion

See [http://ourairports.com/data/](http://ourairports.com/data/) for more information.

## Licensing

Data is in the public domain.

