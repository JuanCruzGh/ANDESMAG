import ee

"""
-Pendiente de terminar!
Codigo modificado para que en lugar de obtenerse SLA se obtenga
la Altura de Emergencia del Detrito (DEA)
"""

def extract_sla_patch(image, SRTM, ALOS, ING):
    """
    Extracts Debris Emergency Altitute (DEA) patch from an image.
    """

    ing_id = image.get("ING_ID")
    otsu = image.get("otsu")
    dem_info = image.get("deminfo")

    geometry = ING.filterMetadata("ID_local", "equals", ing_id)

    # DEM Selection
    dem_1 = SRTM.select("elevation").rename("AVE_DSM").clip(geometry)
    dem_2 = ALOS.select("AVE_DSM").clip(geometry)

    dem_selector = ee.Algorithms.IsEqual(ee.String(dem_info), ee.String("ALOS"))
    dem_selection = ee.Image(ee.Algorithms.If(dem_selector, dem_2, dem_1))
    dem_glacier = dem_selection

    # Function to calculate the area of a band without masked pixels
    def calculate_area(img):
        pixel_area = img.select("AVE_DSM").multiply(ee.Image.pixelArea())
        return pixel_area.reduceRegion(
            **{
                "reducer": ee.Reducer.sum(),
                "geometry": geometry,
                # "scale": 20,
                "scale": 30,
                "maxPixels": 1e8,
                "bestEffort": True,
            }
        ).getNumber("AVE_DSM")

    # Combine classes from classified image
    classified = image
    masks = [classified.select("classification").neq(i) for i in [-1, 7, 4, 2, 8]]
    for mask in masks:
        classified = classified.updateMask(mask).clip(geometry)

    # Reproject the DEM and classified image once to use the same projection
    crs_transform = classified.select("classification").projection()
    dem_glacier = dem_glacier.reproject(crs_transform)
    classified = classified.reproject(crs_transform)

    elevation = dem_glacier.select("AVE_DSM").clip(geometry)

    # Combine snow and shadow on snow (sos)
    snow_mask = classified.select("classification").eq(1).max(classified.select("classification").eq(6))

    # Select debris class
    debrisclass = classified.select("classification").eq(3)
    debris_mask = debrisclass

    # Combine ice and shadow on ice (soi)
    ice_mask = classified.select("classification").eq(0).max(classified.select("classification").eq(5))

    # Mask ice, snow, and debris elevation
    elev_class_ice = elevation.mask(ice_mask.clip(geometry))
    elev_class_snow = elevation.mask(snow_mask.clip(geometry))
    elev_class_debris = elevation.mask(debris_mask.clip(geometry))

    # Create raster images to vectorize
    snow_vec = classified.mask(snow_mask).select("classification").multiply(0).unmask(-10).clip(geometry)
    ice_vec = classified.mask(ice_mask).select("classification").add(10).unmask(-10).clip(geometry)
    vector_image = snow_vec.max(ice_vec)

    debris_vec = classified.mask(debrisclass).select("classification").add(10).unmask(-10).clip(geometry)

    # Calculate and store areas for ratio calculations
    ice_area = calculate_area(elev_class_ice)
    snow_area = calculate_area(elev_class_snow)
    ice_snow_area = ice_area.add(snow_area)
    
    snow_part = snow_area.divide(ice_snow_area)
    void_part = ee.Number(1).subtract(
        (
            ee.Number(ice_area)
            .add(ee.Number(snow_area))
            .divide(calculate_area(elevation))
        )
    )
    
    # Vectorize the classified map with snow and ice patches
    classes = vector_image.reduceToVectors(
        **{
            "reducer": ee.Reducer.countEvery(),
            "geometry": geometry,
            # "scale": 20,
            "scale": 30,
            "eightConnected": False,
            "bestEffort": True,
            "maxPixels": 1e9,
        }
    )
    
    debris_classes2 = debris_vec.reduceToVectors(
        **{
            "reducer": ee.Reducer.countEvery(),
            "geometry": geometry,
            # "scale": 20,
            "scale": 30,
            "eightConnected": False,
            "bestEffort": True,
            "maxPixels": 1e9,
        }
    )

    # Calculate the biggest snow ice patch
    snow_ice_vector_map = ee.FeatureCollection(classes)
    debris_vector_map = ee.FeatureCollection(debris_classes2)
    
    snow_filter = ee.Filter.eq("label", 0)
    snow_max_collection = snow_ice_vector_map.filter(snow_filter).sort("count", False)
    snow_area_vec = ee.Number(snow_max_collection.aggregate_sum("count"))
    snow_max = ee.Feature(snow_max_collection.first())

    ice_filter = ee.Filter.greaterThanOrEquals("label", 9)
    debris_filter = ee.Filter.greaterThanOrEquals("label", 9)

    ice_max_collection = snow_ice_vector_map.filter(ice_filter).sort("count", False)
    debris_max_collection = debris_vector_map.filter(debris_filter).sort("count", False)
    
    debris_area_vec = ee.Number(debris_max_collection.aggregate_sum("count"))

    ice_max = ee.Feature(ice_max_collection.first())
    debris_max = ee.Feature(debris_max_collection.first())
    
    is_ice_null = ee.Feature(None).set("count", 0)
    ice_max = ee.Feature(ee.Algorithms.If(ice_max, ice_max, is_ice_null))
    
    is_debris_null = ee.Feature(None).set("count", 3)
    debris_max = ee.Feature(ee.Algorithms.If(debris_max, debris_max, is_debris_null))
    
    snow_ice_fc = ee.Algorithms.Collection([snow_max, ice_max])
    ice_debris_fc = ee.Algorithms.Collection([ice_max, debris_max])
    
    snow_patch_area = ee.Algorithms.If(
        snow_max_collection.size(), ee.Number(snow_max.get("count")), 0
    )

    ice_patch_area = ee.Number(ice_max.get("count"))
    total_area = ee.Number(snow_ice_vector_map.aggregate_sum("count"))
    
    snow_area_ratio = snow_area_vec.divide(total_area)

    snow_patch_ratio = ee.Number(snow_patch_area).divide(total_area).multiply(100)
    ice_patch_ratio = ee.Number(ice_patch_area).divide(total_area).multiply(100)

    relevant_area = snow_patch_ratio.add(ice_patch_ratio)
    
    # area_debris_patch = debris_area_vec.multiply(0.0004)
    area_debris_patch = debris_area_vec.multiply(0.0009)    
    
    # glacier_area = total_area.multiply(0.0004)
    glacier_area = total_area.multiply(0.0009)
    
    ratio_debris = debris_area_vec.divide(total_area).multiply(100)
    
    snow_ice_image = snow_ice_fc.reduceToImage(["label"], ee.Reducer.first())
    ice_debris_image = ice_debris_fc.reduceToImage(["label"], ee.Reducer.first())
    
    bigger_ice = snow_ice_image.mask(snow_ice_image.select("first").eq(0)).focal_max(2)
    bigger_debris = ice_debris_image.mask(ice_debris_image.select("first").eq(3)).focal_max(2)
    
    touching_zone = bigger_ice.subtract(
        snow_ice_image.mask(snow_ice_image.select("first").gte(9))
    )
    
    touching_zone_debris = bigger_debris.subtract(
        ice_debris_image.mask(ice_debris_image.select("first").gte(9))
    )
    
    elev_touch = elevation.addBands(touching_zone, ["first"])
    elev_touch_debris = elevation.addBands(touching_zone_debris, ["first"])
    
    elevation_snow_line = elev_touch.mask(elev_touch.select("first").lt(-1))
    elevation_debris_line = elev_touch_debris.mask(elev_touch_debris.select("first").lt(-1))
    
    # Set Snow condition to true when 95% of the snow/ice area is covered with snow
    snow_cond = snow_part.gt(0.95)
    
    mean_altitudes = elevation_snow_line.reduceRegion(
        **{
            "reducer": ee.Reducer.median(),
            "maxPixels": 1e8,
            "geometry": geometry,
            "bestEffort": True,
        }
    )
    
    mean_altitudes_debris = elevation_debris_line.reduceRegion(
        **{
            "reducer": ee.Reducer.median(),
            "maxPixels": 1e8,
            "geometry": geometry,
            "bestEffort": True,
        }
    )

    lowest_snow_elev = ee.Number(
        elevation.clip(snow_max).reduceRegion(
            **{
                "reducer": ee.Reducer.min(),
                "geometry": geometry,
                # "scale": 20,
                "scale": 30,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )
    
    lowest_ice_elev = ee.Number(
        elevation.clip(ice_max).reduceRegion(
            **{
                "reducer": ee.Reducer.min(),
                "geometry": geometry,
                # "scale": 20,
                "scale": 30,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )

    lowest_sla = ee.Number(
    elevation.reduceRegion(
        **{
            "reducer": ee.Reducer.min(),
            "geometry": geometry,
            # "scale": 20,
            "scale": 30,
            "bestEffort": True,
        }
    ).get("AVE_DSM")
    )
    
    highest_sla = ee.Number(
        elevation.reduceRegion(
            **{
                "reducer": ee.Reducer.max(),
                "geometry": geometry,
                # "scale": 20,
                "scale": 30,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )

    no_touch = ee.Number(
        ee.Algorithms.If(snow_max_collection.size(), lowest_snow_elev, highest_sla)
    )
    
    no_touch_debris = ee.Number(
        ee.Algorithms.If(ice_max_collection.size(), lowest_ice_elev, highest_sla)
    )

    snow_line_1 = mean_altitudes.get("AVE_DSM")
    debris_line_1 = mean_altitudes_debris.get("AVE_DSM")
    
    snow_line_2 = ee.Algorithms.If(snow_line_1, snow_line_1, no_touch)
    debris_line_2 = ee.Algorithms.If(debris_line_1, debris_line_1, no_touch_debris)
    
    snow_line = ee.Number(ee.Algorithms.If(snow_cond, lowest_sla, snow_line_2))
    debris_line = ee.Number(ee.Algorithms.If(snow_cond, lowest_sla, debris_line_2))
    
    #stD issues
    # Calcular desviación estándar para la línea de nieve
    snow_line_std_dev = ee.Number(
        elevation_snow_line.reduceRegion(
            reducer=ee.Reducer.stdDev(),
            geometry=geometry,
            scale=30,
            maxPixels=1e8,
            bestEffort=True
        ).getNumber("AVE_DSM")
    )
    
    # Calcular desviación estándar para la línea de escombros
    debris_line_std_dev = ee.Number(
        elevation_debris_line.reduceRegion(
            reducer=ee.Reducer.stdDev(),
            geometry=geometry,
            scale=30,
            maxPixels=1e8,
            bestEffort=True
        ).getNumber("AVE_DSM")
    )
    
    image_date = ee.Number(classified.get("system_time_start"))
       
    shorten = image_date.divide(1000).floor().divide(86400).add(25569)
    
    feature = ee.Feature(None)
    feature = (
        feature.set("Snow Cover Ratio", snow_area_ratio)
        .set("Snow Line Altitude-msnm", snow_line)
        .set("Debris Emergency Altitude-msnm", debris_line)
        .set("Area-km2", glacier_area)    
        .set("Ratio Area v/o Snow or Ice", void_part)
        .set("system:time_start", image_date)
        .set("date_MSxlsx", shorten)
        .set("otsu", otsu)
        .set("Considered Area for MP-SLA Extraction", relevant_area)
        .set("stdDev SLA, 0 means no touch between Main patches [m]", snow_line_std_dev)
        .set("stdDev DEA, 0 means no touch between Main patches [m]", debris_line_std_dev)
        .set("ID_Glacier", ing_id)
        .set("Debris area km2", area_debris_patch)
        .set("Debris area ratio", ratio_debris)
    )

    return  feature
