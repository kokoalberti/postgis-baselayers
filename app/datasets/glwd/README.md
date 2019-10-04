# Global Lakes and Wetlands Database

## Description

Drawing upon a variety of existing maps, data and information, WWF and the Center for Environmental Systems Research, University of Kassel, Germany created the Global Lakes and Wetlands Database (GLWD). The combination of best available sources for lakes and wetlands on a global scale (1:1 to 1:3 million resolution), and the application of GIS functionality enabled the generation of a database which focuses in three coordinated levels on (1) large lakes and reservoirs, (2) smaller water bodies, and (3) wetlands.

More information: [GLWD_Data_Documentation.pdf](GLWD_Data_Documentation.pdf)

### glwd_level_1

Level 1 (GLWD-1) comprises the 3067 largest lakes (area ≥ 50 km2) and 654 largest reservoirs (storage capacity ≥ 0.5 km3) worldwide, and includes extensive attribute data.

More information: [https://www.worldwildlife.org/publications/global-lakes-and-wetlands-database-large-lake-polygons-level-1](https://www.worldwildlife.org/publications/global-lakes-and-wetlands-database-large-lake-polygons-level-1)

### glwd_level_2

Level 2 (GLWD-2) comprises permanent open water bodies with a surface area ≥ 0.1 km2 excluding the water bodies contained in GLWD-1. 

More information: [https://www.worldwildlife.org/publications/global-lakes-and-wetlands-database-small-lake-polygons-level-2](https://www.worldwildlife.org/publications/global-lakes-and-wetlands-database-small-lake-polygons-level-2)

## Examples

### Find all reservoirs in Canada used for flood control

Query:

    select dam_name
    from glwd.glwd_level_1
    where
      type = 'Reservoir'
      and country = 'Canada'
      and (use_1 = 'c' or use_2 = 'c' or use_3 = 'c')

Returns:

        dam_name
    ---------------
    Jenpeg
    Rapide-Des-Cedres
    Mitchinamecus
    Duncan
    Brazeau
    

## Attribution

See [https://www.worldwildlife.org/pages/global-lakes-and-wetlands-database#](https://www.worldwildlife.org/pages/global-lakes-and-wetlands-database#) for more information.

## Licensing

The data is available for free download (for non-commercial scientific, conservation and educational purposes).

More information: [GLWD_Data_Disclaimer.pdf](GLWD_Data_Disclaimer.pdf)
