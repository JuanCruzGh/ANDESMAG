import ee
import pandas as pd

"""
Codigo modificado para que en lugar de obtenerse SLA se obtenga
la Altura de Emergencia del Detrito (DEA)
"""

def extract_sla_patch(image, SRTM, ALOS, ING): # ADAPT (!)
    """
    Extracts Debris Emergency Altitute (DEA) patch from an image.
    """

    ing_id = image.get("ING_ID")    # En el original esta fuera de la funcion esta variable
    otsu = image.get("otsu")        # En el original esta fuera de la funcion esta variable
    dem_info = image.get("deminfo") #NEW

    # TODO CHECK IF THIS (SHOULD BE ING)
    geometry = ING.filterMetadata("ID_local", "equals", ing_id)

    # DEM Selection
    dem_1 = SRTM.select("elevation").rename("AVE_DSM").clip(geometry)
    dem_2 = ALOS.select("AVE_DSM").clip(geometry) #NEW!

    dem_selector = ee.Algorithms.IsEqual(ee.String(dem_info), ee.String("ALOS")) #NEW!
    dem_selection = ee.Image(ee.Algorithms.If(dem_selector, dem_2, dem_1)) # NEW
    dem_glacier = dem_selection
    
    # Funcion para calcular las áreas
    def calculate_area(img):
        """
        Helper method to calculate the area of a band without masked pixels.
        """

        # Take a band (elevation in this case) to calculate the area
        pixel_area = img.select("AVE_DSM").multiply(ee.Image.pixelArea())
        return pixel_area.reduceRegion(
            **{
                "reducer": ee.Reducer.sum(),  # type: ignore
                "geometry": geometry,
                "scale": 20,
                # "scale": 30, #NEW
                "maxPixels": 1e8,
                "bestEffort": True,
            }
        ).getNumber("AVE_DSM")

    
    # Combine classes from classified image

    classified = image
    dcmask = classified.select("classification").neq(-1)  # Unclassified
    mask1 = classified.select("classification").neq(7)  # All but shadow on water
    mask2 = classified.select("classification").neq(4)  # All but clouds
  #  mask3 = classified.select("classification").neq(3)  # All but debris cover
    mask4 = classified.select("classification").neq(2)  # All but water
    mask5 = classified.select("classification").neq(8)

    classified = (
        classified.mask(dcmask)
        .clip(geometry)
        .updateMask(mask1)
        .clip(geometry)
        .updateMask(mask2)
        .clip(geometry)
      #  .updateMask(mask3)
      #  .clip(geometry)
        .updateMask(mask4)
        .clip(geometry)
        .updateMask(mask5)
        .clip(geometry)
    )

    # Elevation analysis
    # changes projection; esto en el código original (GEE) no está
    crs_transform = classified.select("classification").projection()
    dem_glacier = dem_glacier.reproject(crs_transform)
    classified = classified.reproject(crs_transform) 
    elevation = dem_glacier.select("AVE_DSM").clip(geometry)

    # Combine snow and shadow on snow (sos)
    single_class_snow = classified.select("classification").eq(1)
    single_class_sos = classified.select("classification").eq(6)
    snow_mask = single_class_snow.max(single_class_sos)
    
    # Select debris class
    debrisclass = classified.select("classification").eq(3)
    
    # Debris Class mask; NEW!
    debris_mask = debrisclass
    
    # Combine ice and shadow on ice (soi)
    single_class_ice = classified.select("classification").eq(0)
    single_class_soi = classified.select("classification").eq(5)
    ice_mask = single_class_ice.max(single_class_soi)

    # Mask ice
    elev_class_ice = elevation.mask(ice_mask.clip(geometry))

    # Mask snow
    elev_class_snow = elevation.mask(snow_mask.clip(geometry))
    
    # Mask debris elevation; NEW!
    elev_class_debris = elevation.mask(debris_mask.clip(geometry))

    # Create raster image to vectorize (snow and Ice)
    snow_vec = (
        classified.mask(snow_mask)
        .select("classification")
        .multiply(0)
        .unmask(-10)
        .clip(geometry)
    )

    ice_vec = (
        classified.mask(ice_mask)
        .select("classification")
        .add(10)
        .unmask(-10)
        .clip(geometry)
    )

    vector_image = snow_vec.max(ice_vec)
    
    # Create raster image to vectorize (debris covered)
    debris_vec = (
        classified.mask(debrisclass)
        .select("classification")
        .add(10)
        .unmask(-10)
        .clip(geometry)
    )

    # Calculate and store Areas for Ratio calculations

    ice_area = calculate_area(elev_class_ice) # Esta variable deberia entregar un numero positivo
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
    
    #NEW!
    
    # Set Snow condition to true when 95% of the snow/ice area is covered with snow
    # With this condition the SnowLine is set to the minimal altitude of the glacier-
    # outline area
    snow_cond = snow_part.gt(0.95)

    # Calculate lowest / highest possible SLA's

    lowest_sla = ee.Number(
        elevation.reduceRegion(
            **{
                "reducer": ee.Reducer.min(),  # type: ignore
                "geometry": geometry,
                "scale": 20,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )

    highest_sla = ee.Number(
        elevation.reduceRegion(
            **{
                "reducer": ee.Reducer.max(),  # type: ignore
                "geometry": geometry,
                "scale": 20,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )

    # Vectorize the classified map with snow and ice patches
    classes = vector_image.reduceToVectors(
        **{
            "reducer": ee.Reducer.countEvery(),  # type: ignore
            "geometry": geometry,
            # "scale": 30, # NEW!
            "scale": 20, # NEW!; en GEE sale con 20
            "eightConnected": False,
            "bestEffort": True,
            "maxPixels": 1e9,
        }
    )
    
    # Vectorize the classified map with debris
    # debrisclass = debris_vec.reduceToVectors( # Le cambie el nombre como esta en GEE
                                                # para no renombrar debrisclass
    debris_classes2 = debris_vec.reduceToVectors(  #NEW!
        **{
            "reducer": ee.Reducer.countEvery(),  # type: ignore
            "geometry": geometry,
            "scale": 20, # NEW!; en GEE sale con 20
            "eightConnected": False,
            "bestEffort": True,
            "maxPixels": 1e9,
        }
    )

    # Calculate the biggest snow ice patch
    snow_ice_vector_map = ee.FeatureCollection(classes)
    debris_vector_map = ee.FeatureCollection(debris_classes2) #equivalente a "result2"
    
    snow_filter = ee.Filter.eq("label", 0)
    snow_max_collection = snow_ice_vector_map.filter(snow_filter).sort("count", False)
    snow_area_vec = ee.Number(snow_max_collection.aggregate_sum("count"))
    snow_max = ee.Feature(snow_max_collection.first())

    ice_filter = ee.Filter.greaterThanOrEquals("label", 9)
    debris_filter = ee.Filter.greaterThanOrEquals('label',9)
    # debris_filter = ee.Filter.greaterThan('label',0) prueba!

    ice_max_collection = snow_ice_vector_map.filter(ice_filter).sort("count", False)
    debris_max_collection = debris_vector_map.filter(debris_filter).sort("count", False) #equivale a maxdebris1
    
    
    # ice_area_vec = ee.Number(ice_max_collection.aggregate_sum("count"))
    debris_area_vec = ee.Number(debris_max_collection.aggregate_sum("count")) # Este parece que esta dando mal!
    
    ice_max = ee.Feature(ice_max_collection.first())
    debris_max = ee.Feature(debris_max_collection.first()) #NEW
    
    # Check this implementation Essentially nulls are being replace with a conditional
    is_ice_null = ee.Feature(None).set("count", 0)
    ice_max = ee.Feature(ee.Algorithms.If(ice_max, ice_max, is_ice_null))
    
    is_debris_null = ee.Feature(None).set("count", 3) #NEW
    debris_max = ee.Feature(ee.Algorithms.If(debris_max, debris_max, is_debris_null)) #NEW
    
    snow_ice_fc = ee.Algorithms.Collection([snow_max, ice_max])
    ice_debris_fc = ee.Algorithms.Collection([ice_max, debris_max]) # NEW
    
    snow_patch_area = ee.Algorithms.If(
        snow_max_collection.size(), ee.Number(snow_max.get("count")), 0
    )

    ice_patch_area = ee.Number(ice_max.get("count"))
    total_area = ee.Number(snow_ice_vector_map.aggregate_sum("count"))
    
    snow_area_ratio = snow_area_vec.divide(total_area)

    snow_patch_ratio = ee.Number(snow_patch_area).divide(total_area).multiply(100)
    ice_patch_ratio = ee.Number(ice_patch_area).divide(total_area).multiply(100)

    relevant_area = snow_patch_ratio.add(ice_patch_ratio)
    
    # Debris covered area calculation (km2)
    area_debris_patch =  debris_area_vec.multiply(0.0004)
    
    # glacier area calculation (km2)
    glacier_area = total_area.multiply(0.0004)
    
    # ration of debris covered area %
    ratio_debris = debris_area_vec.divide(total_area).multiply(100)
    
    # Extract the zone where the two patches touch each other

    snow_ice_image = snow_ice_fc.reduceToImage(["label"], ee.Reducer.first())  # type: ignore
    ice_debris_image = ice_debris_fc.reduceToImage(["label"], ee.Reducer.first()) #NEW
    
    bigger_ice = snow_ice_image.mask(snow_ice_image.select("first").eq(0)).focal_max(2)
    bigger_debris = ice_debris_image.mask(ice_debris_image.select("first").eq(3)).focal_max(2) #NEW
    
    touching_zone = bigger_ice.subtract(
        snow_ice_image.mask(snow_ice_image.select("first").gte(9))
    )
    
    touching_zone_debris = bigger_debris.subtract(
        ice_debris_image.mask(ice_debris_image.select("first").gte(9))
    )                                                                       #NEW
    
    elev_touch = elevation.addBands(touching_zone, ["first"])
    elev_touch_debris = elevation.addBands(touching_zone_debris, ["first"])    #NEW
    
    elevation_snow_line = elev_touch.mask(elev_touch.select("first").lt(-1))
    elevation_debris_line = elev_touch_debris.mask(elev_touch_debris.select("first").lt(-1))    #NEW
    
    # Calculate mean altitude of the zone where the patches touch
    mean_altitudes = elevation_snow_line.reduceRegion(
        **{
            "reducer": ee.Reducer.median(),  # type: ignore
            "maxPixels": 1e8,
            "geometry": geometry,
            "bestEffort": True,
        }
    )
    
    # NEW
    mean_altitudes_debris = elevation_debris_line.reduceRegion(
        **{
            "reducer": ee.Reducer.median(),  # type: ignore
            "maxPixels": 1e8,
            "geometry": geometry,
            "bestEffort": True,
        }
    ) # NEW

    # Exception Handling

    lowest_snow_elev = ee.Number(
        elevation.clip(snow_max).reduceRegion(
            **{
                "reducer": ee.Reducer.min(),  # type: ignore
                "geometry": geometry,
                "scale": 20,
                "bestEffort": True,
            }
        )
    )
    
    # Exception Handling # NEW

    lowest_ice_elev = ee.Number(
        elevation.clip(ice_max).reduceRegion(
            **{
                "reducer": ee.Reducer.min(),  # type: ignore
                "geometry": geometry,
                "scale": 20,
                "bestEffort": True,
            }
        )
    )   # NEW

    no_touch = ee.Number(
        ee.Algorithms.If(snow_max_collection.size(), lowest_snow_elev, highest_sla)
    )
    
    # el valor de lowest_ice_elev a no_touch_debris si la colección ice_max_collection tiene elementos. 
    # De lo contrario, asigna el valor de highest_sla a no_touch_debris. 
    # La función ee.Algorithms.If se utiliza para realizar esta asignación condicional en función del 
    # tamaño de la colección. NEW!
    no_touch_debris = ee.Number(
        ee.Algorithms.If(ice_max_collection.size(), lowest_ice_elev, highest_sla)
    ) # NEW


    snow_line_1 = mean_altitudes.get("AVE_DSM")
    debris_line_1 = mean_altitudes_debris.get("AVE_DSM") #NEW
    
    snow_line_2 = ee.Algorithms.If(snow_line_1, snow_line_1, no_touch)
    debris_line_2 = ee.Algorithms.If(debris_line_1, debris_line_1, no_touch_debris) #NEW; (!) 
    # CREO QUE ACA ESTA EL PROBLEMA DE AVE_DSM, TENGO QUE VER COMO LO ESTA OBTENIENDO

    snow_line = ee.Number(ee.Algorithms.If(snow_cond, lowest_sla, snow_line_2))
    debris_line = ee.Number(ee.Algorithms.If(snow_cond, lowest_sla, debris_line_2)) #NEW
    # Basicamente si el 95% de la imagen es nieve, va a tomar el valor más bajo del parche
    # de nieve
    
    snow_line_std_dev = ee.Number(
        elevation_snow_line.reduceRegion(
            **{
                "reducer": ee.Reducer.stdDev(),  # type: ignore
                "maxPixels": 1e8,
                "geometry": geometry,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )
    
    # NEW; (!) QUIZAS SI TIENE EL RESULTADO {AVE_DSM=4957} NO PUEDE HACER ESTADÍSTICA DE UN STR
    debris_line_std_dev = ee.Number(
        elevation_debris_line.reduceRegion(
            **{
                "reducer": ee.Reducer.stdDev(),  # type: ignore
                "maxPixels": 1e8,
                "geometry": geometry,
                "bestEffort": True,
            }
        ).get("AVE_DSM")
    )

    # Check if 95% of the glacier is convered with snow by settings SLA to the lowest
    # elevation of the glacier
    coverage_95 = ee.Algorithms.If(snow_cond, 0, snow_line_std_dev)
    coverage_95_debris = ee.Algorithms.If(snow_cond, 0, debris_line_std_dev) #NEW
    
    std_dev_sla = ee.Algorithms.If(mean_altitudes.size(), coverage_95, 0)
    std_dev_debris_altitude = ee.Algorithms.If(mean_altitudes_debris.size(), coverage_95_debris, 0)

    # Add date in MS-Excel readable format
    image_date = ee.Number(classified.get("system_time_start"))
       
    shorten = image_date.divide(1000).floor().divide(86400).add(25569)
    
    # Create feature to return and export information in a table (eg CSV)
    # (!) MODIFICAR LA SALIDA DE ESTAS VARIABLES
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
        .set("stdDev SLA, 0 means no touch between Main patches [m]", std_dev_sla)
        .set("stdDev DEA, 0 means no touch between Main patches [m]", std_dev_debris_altitude)
        .set("ID_Glacier", ing_id)
        .set("Debris area km2", area_debris_patch)
        .set("Debris area ratio",ratio_debris)
        
    )

    return  feature    


