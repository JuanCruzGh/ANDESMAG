import ee


def extract_sla_patch(image, SRTM, ALOS, ING):
    
    id_glacier = image.get("ING_ID")
    otsu = image.get("otsu")
    dem_info = image.get("deminfo")
    
    geometry = ING.filterMetadata("rgi_id", "equals", id_glacier )
    
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
    debris_mask = classified.select("classification").eq(3)
    
    # Combine ice and shadow on ice (soi)
    ice_mask = classified.select("classification").eq(0).max(classified.select("classification").eq(5))
    
    # Mask ice, snow, and debris elevation
    elev_class_ice = elevation.mask(ice_mask.clip(geometry))
    elev_class_snow = elevation.mask(snow_mask.clip(geometry))
    elev_class_debris = elevation.mask(debris_mask.clip(geometry))
    
    # Create raster images to vectorize; Genero los raster para trabajar con la colección nieve-hielo
    snow_vec = classified.mask(snow_mask).select("classification").multiply(0).unmask(-10).clip(geometry)
    ice_vec = classified.mask(ice_mask).select("classification").add(10).unmask(-10).clip(geometry)
    # Vectorizo el conjunto nieve-hielo
    vector_image = snow_vec.max(ice_vec)
    
    # Create raster images to vectorize; Genero los raster para trabajar con la colección hielo-detrito
    ice_vec2 = classified.mask(ice_mask).select("classification").multiply(0).unmask(-10).clip(geometry) # NEW FOR DEE 
    debris_vec = classified.mask(debris_mask).select("classification").add(10).unmask(-10).clip(geometry) # NEW FOR DEE 
    # Vectorizo el conjunto hielo-detrito
    vector_image2 = ice_vec2.max(debris_vec) # NEW FOR DEE 
    
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
    
    classes2 = vector_image2.reduceToVectors(  # NEW FOR DEE 
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
    
    # Calculate the biggest snow ice patch and biggest ice debris patch
    snow_ice_vector_map = ee.FeatureCollection(classes)
    ice_debris_vector_map = ee.FeatureCollection(classes2)  # NEW FOR DEE 
    
    # Defino filtro aquellos píxeles cuyo valor es igual a 0 en conjunto nieve-hielo
    snow_filter = ee.Filter.eq("label", 0)
    # Aplico el filtro de 0 (nieve) y ordeno los parches de nieve de mayor a menor
    snow_max_collection = snow_ice_vector_map.filter(snow_filter).sort("count", False)
    # Calcula el area total del parche mas grande de nieve
    snow_area_vec = ee.Number(snow_max_collection.aggregate_sum("count"))
    # Obtengo el parche de mayor tamaño de nieve en en conjunto nieve-hielo
    snow_max = ee.Feature(snow_max_collection.first())
    
    # Defino filtro aquellos píxeles de hielo cuyo valor es mayor o igual a 9 para hielo en la colección nieve-hielo
    ice_filter = ee.Filter.greaterThanOrEquals("label", 9)
    # De la colección nieve-hielo filtro solo el parche de hielo y ordeno de mayor a menor area
    ice_max_collection = snow_ice_vector_map.filter(ice_filter).sort("count", False)
    # Obtengo el parche mas grande de hielo de la colección nieve-hielo
    ice_max = ee.Feature(ice_max_collection.first())
    
    
    # Defino filtro aquellos píxeles de hielo cuyo valor es mayor o igual a 9 para hielo en la colección hielo-detrito
    debris_filter = ee.Filter.greaterThan("label", 9) # NEW FOR DEE
    # Defino filtro aquellos píxeles cuyo valor es igual a 0 en conjunto hielo-detrito # NEW FOR DEE
    ice_filter2 = ee.Filter.eq("label", 0) # NEW FOR DEE
    
    # Aplico el filtro de 0 (hielo) y ordeno los parches de hielo de mayor a menor # NEW FOR DEE
    ice_max_collection2 = ice_debris_vector_map.filter(ice_filter2).sort("count", False) # NEW FOR DEE 
    # Calcula el area total del parche mas grande de hielo  # NEW FOR DEE 
    ice_area_vec2 = ee.Number(ice_max_collection2.aggregate_sum("count")) # NEW FOR DEE 
    # Obtengo el parche de mayor tamaño de hielo en conjunto hielo-detrito # NEW FOR DEE 
    ice_max2 = ee.Feature(ice_max_collection2.first()) # NEW FOR DEE
    
    # De la colección hielo-detrito filtro solo el parche de detrito y ordeno de mayor a menor area
    debris_max_collection = ice_debris_vector_map.filter(debris_filter).sort("count", False)
    # Calcula el area total del parche mas grande de detrito
    debris_area_vec = ee.Number(debris_max_collection.aggregate_sum("count"))
    # Obtengo el parche mas grande de detrito de la colección hielo-detrito
    debris_max = ee.Feature(debris_max_collection.first())
    
    # Me aseguro que ice_max siempre sea un objeto ee.Feature
    is_ice_null = ee.Feature(None).set("count", 0)
    ice_max = ee.Feature(ee.Algorithms.If(ice_max, ice_max, is_ice_null))
    
    # Me aseguro que debris_max siempre sea un objeto ee.Feature; no hace falta!
    # is_debris_null = ee.Feature(None).set("count", 3)
    # debris_max = ee.Feature(ee.Algorithms.If(debris_max, debris_max, is_debris_null))
    
    # Organizo y almaceno los resultados de los mayores parches encontrados en la coleccion nieve-hielo
    snow_ice_fc = ee.Algorithms.Collection([snow_max, ice_max])
    # Organizo y almaceno los resultados de los mayores parches encontrados en la coleccion hielo-detrito
    ice_debris_fc = ee.Algorithms.Collection([ice_max2, debris_max])
    
    # asigna a snow_patch_area el valor de snow_max.get("count") si snow_max_collection 
    # tiene elementos, o 0 si no tiene elementos
    snow_patch_area = ee.Algorithms.If(
        snow_max_collection.size(), ee.Number(snow_max.get("count")), 0
    )
    
    # área del mayor parche de hielo encontrado en colección nieve-hielo
    ice_patch_area = ee.Number(ice_max.get("count"))
    # suma total de áreas de todos los parches de nieve y hielo en colección nieve-hielo
    total_area = ee.Number(snow_ice_vector_map.aggregate_sum("count"))
    # ratio entre el area nevada y el area total
    snow_area_ratio = snow_area_vec.divide(total_area)
    
    # porcentaje del área total que cubre el parche de nieve más grande encontrado en la imagen
    snow_patch_ratio = ee.Number(snow_patch_area).divide(total_area).multiply(100)
    # porcentaje del área total que cubre el parche de hielo más grande encontrado en la imagen
    ice_patch_ratio = ee.Number(ice_patch_area).divide(total_area).multiply(100)
    #  porcentaje total del área de interés (parches de nieve y hielo) dentro del área total de la imagen.
    relevant_area = snow_patch_ratio.add(ice_patch_ratio)
    # Area ocupada por detritos
    area_debris_patch = debris_area_vec.multiply(0.0009)    
    # Area total del glaciar (usa la colección nieve-hielo) contabiliza todos los píxeles
    glacier_area = total_area.multiply(0.0009)
    # Ratio detritos / area total
    ratio_debris = debris_area_vec.divide(total_area).multiply(100)
    
    # Crea una imagen raster donde cada píxel tiene el valor de la etiqueta (label) de la coleccion nieve-hielo
    snow_ice_image = snow_ice_fc.reduceToImage(["label"], ee.Reducer.first())
    # Crea una imagen raster donde cada píxel tiene el valor de la etiqueta (label) de la coleccion hielo-detrito
    ice_debris_image = ice_debris_fc.reduceToImage(["label"], ee.Reducer.first())
    
    # Obtengo el parche mas grande de hielo de la colección nieve-hielo
    bigger_ice = snow_ice_image.mask(snow_ice_image.select("first").eq(0)).focal_max(2)
    # Obtengo el parche mas grande de detrito de la colección hielo-detrito
    bigger_debris = ice_debris_image.mask(ice_debris_image.select("first").eq(0)).focal_max(2)
    
    # Areas donde  el parche más grandes de hielo están en contacto con otras 
    # clases específicas de la imagen (snow_ice_image) que cumplen con la condición de ser 
    # de interés (en este caso, first mayor o igual a 9)
    touching_zone = bigger_ice.subtract(
        snow_ice_image.mask(snow_ice_image.select("first").gte(9))
    )
    
    # Areas donde el parche más grandes de detrito están en contacto con otras 
    # clases específicas de la imagen (ice_debris_image) que cumplen con la condición de ser 
    # de interés (en este caso, first mayor o igual a 9)
    touching_zone_debris = bigger_debris.subtract(
        ice_debris_image.mask(ice_debris_image.select("first").gte(9))
    )
    
    # Agrego la banda con la información altitudinal en las zonas de contacto
    elev_touch = elevation.addBands(touching_zone, ["first"])
    elev_touch_debris = elevation.addBands(touching_zone_debris, ["first"])
    
    # Agrego la banda con la información altitudinal en las zonas de contacto 
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
           
    
    image_date = ee.Date(classified.get("system_time_start"))
    formatted_date = image_date.format("dd-MM-yyyy")
    
    # Calcula el área total en metros cuadrados del polígono
    geometry_area = geometry.geometry().area().divide(1e6)  # en km2
    
    # Calcula el porcentaje de cobertura
    coverage_pct = ee.Number(glacier_area).divide(geometry_area).multiply(100)
    
    feature = ee.Feature(None)
    feature = (
        feature.set("glacier_id", id_glacier )
        .set("snow_cover_ratio", snow_area_ratio)
        .set("snow_line_altitude_masl", snow_line)
        .set("debris_area_ratio", ratio_debris)
        .set("debris_emergence_elevation_masl", debris_line)
        .set("total_area_km2", glacier_area) 
        .set("std_dev_sla_m", snow_line_std_dev)
        .set("std_dev_dee_m", debris_line_std_dev)
        .set("system:time_start", image_date)
        .set("date", formatted_date)
        .set("ratio_area_vs_snow_or_ice", void_part)
        .set("considered_area_for_MP_extraction", relevant_area)
        .set("otsu", otsu)
        .set("img_coverage_pct", coverage_pct)
    )
    
    return  feature
