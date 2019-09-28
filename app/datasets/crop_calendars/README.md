# Crop Calendars

Global crop calendar datasets

## Description

Data stored in `crop_calendars` schema, with the calendars by Sacks et al. (based in turn on FAO/GIEWS/USGS) in the `sacks_crop_calendar` table. 

## Examples

Find crop calendars for a location in Kenya:

    SELECT 
         location, 
    	 crop, 
    	 "full.crop.name" AS crop_full,
    	 "crop.name.in.original.data" AS crop_long,
    	 "plant.start" AS plant_start,
    	 "plant.end" AS plant_end,
    	 "harvest.start" AS harvest_start,
    	 "harvest.end" AS harvest_end 
    FROM 
         crop_calendars.sacks_crop_calendar 
    WHERE 
         ST_Intersects(
            sacks_crop_calendar.geom, 
            ST_SetSRID(ST_Point(38.0, 0.0), 4326)
         );

## Attribution

Sacks, W.J., D. Deryng, J.A. Foley, and N. Ramankutty (2010). Crop planting dates: An analysis of global patterns. Global Ecology and Biogeography, 19: 607-620.

## License


