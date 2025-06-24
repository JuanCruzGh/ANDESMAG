"""
    Main code to process, make the facies map, 
    and extract the SLA (snow Line Altitude)
    and DEA/DEE (debris emergence altitude)
    for glacier larger than 0.1 k2 from the National 
    Glacier Inventory of Argentina.
"""
# --------------------------- EXTERNAL MODULES -------------------------------#
import ee
import geemap
import os
import time

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()

# --------------------------- INTERNAL MODULES -------------------------------#

from source.prep_final_rgi import PreProcessor  
from source.cloud_shadow_mask_rgi import add_cloud_shadow 
from source.hill_shadow import add_hill_shadow 
from source.classifier_rgi import decision_tree 
from source.main_patches_debris_rgi import extract_sla_patch
from source.utils_main import (
    write_to_local,
    write_sla_data,
    write_sla_dataDrive,
    convert_to_float
)
from source.thresholds import (
    THRESHOLD_CLOUD_SCORE,
    THRESHOLD_ADD_CLOUD_SCORE,
    THRESHOLD_ADD_CLOUD_SHADOW,
    THRESHOLD_DECISION_TREE
)

from source.config import (
    asset, id_glacier_list, batch, doy_start, doy_end, hs_start, hs_end,
    cloudiness, coverage, hsboolean, dem,
    export_condition, parent_facies, parent_prep, crs
)

def main():
    
    start = time.time()
    
    print("starting...")
    
    """ 
    
    Define the searching parameters
    
    ING: asset containing the boundaries of the working glaciers; 
        IMPORTANT! this asset must have a column called “ID_local” containing the 
        identifiers of the working glaciers. It connects to the variable “ing_list”.
    
    ing_list : is a test list of glacier to check if the while loop works ok.
              but must to be improved with a list of all the glaciers with more than 0.1 km2
    
    start_year & end_year : initial and end years of analysis
    
    doy_start & doy_end : initial and end day of year (doy) to search  the images
    
    year and doy values must changes through time in the plataform It could be done in another loop
    or using a refreshing time. Right now it is set rigid. But works!
    
    
    cloudiness : percentage. Maximum coverage of cloud over the glacier that is allowed. 
                 It is calculate in the prep.py module.
    
    coverage : percentage. Minimum area of the glacier covered by the image. 
    
    hsboolean: Not very clear what it does.
    
    hs_start & hs_end: initial and end day of year (doy) to calculat the hillshade
    
    STRM & ALOS:  access to dem SRTM and ALOS, respectively.
    
    dem: Digital Elevation DEM used to calculate the hill shade and the SLA.
    
    batch: list of tuples containing the start and end years of each batch; 
    example of wording: if I want to cover from 1990 to 1995 in two batches 
    i write [(1990,1992), (1993, 1995)].
    
    """
    
    # DEM SRTM y ALOS
    SRTM = ee.Image("USGS/SRTMGL1_003")
    ALOS = ee.Image("JAXA/ALOS/AW3D30/V2_2")
    
    index = 0
    
    while index < len(id_glacier_list):
        for i in range(len(batch)):
    
            # Define batch start and end year
            start_year = ee.Number(batch[i][0])
            end_year = ee.Number(batch[i][1])
    
            # Select current glacier ID
            id_glacier = id_glacier_list[index]
    
            # ------------------ PREPROCESSING MODULE ------------------ #
            print("Preprocessing...")
            preprocessor = PreProcessor(
                id_glacier=id_glacier,
                start_year=start_year,
                end_year=end_year,
                doy_start=doy_start,
                doy_end=doy_end,
                cloudiness=cloudiness,
                coverage=coverage,
                hsboolean=hsboolean,
                dem=dem,
                THRESHOLD_CLOUD_SCORE=THRESHOLD_CLOUD_SCORE
            )
            preprocessed = preprocessor.execute(asset)
    
            # ------------------ CLOUD & HILL SHADOW MODULES ------------------ #
            print("Processing cloud shadow mask...")
            preprocessed = preprocessed.map(lambda image: add_cloud_shadow(
                image, asset,
                THRESHOLD_ADD_CLOUD_SHADOW,
                THRESHOLD_ADD_CLOUD_SCORE
            ))
    
            print("Processing hill shadow...")
            preprocessed = add_hill_shadow(
                image_collection=preprocessed,
                hs_start=hs_start,
                hs_end=hs_end
            )
    
            # ------------------ CLASSIFICATION MODULE ------------------ #
            print("Running classifier...")
            map_collection = preprocessed.map(lambda image: decision_tree(
                image, SRTM, asset, THRESHOLD_DECISION_TREE))
    
            # ------------------ Metrics MODULE ------------------ #
            print("Extracting metrics...")
            metrics_collection = map_collection.map(lambda image: extract_sla_patch(
                image, SRTM, ALOS, asset))
            metrics_data = ee.FeatureCollection(metrics_collection)
    
            # ------------------ EXPORT PATHS (LOCAL) ------------------ #
            path_clas = os.path.join(parent_facies, id_glacier)
            path_prep = os.path.join(parent_prep, id_glacier)
    
            if export_condition["Directory"] == "Local":
                os.makedirs(path_clas, exist_ok=True)
                os.makedirs(path_prep, exist_ok=True)
    
            # Convert to appropriate format for export
            convert_collection = map_collection.map(ee.Image.int8)
            convert_preprocessed = preprocessed.map(convert_to_float)
    
            # ------------------ EXPORT IMAGES (PREPROCESSED) ------------------ #
            if export_condition["IMG"] == "Y":
                print("Exporting preprocessed images...")
                if export_condition["Directory"] == "Local":
                    write_to_local(response=convert_preprocessed, path=path_prep)
                elif export_condition["Directory"] == "Drive":
                    geemap.ee_export_image_collection_to_drive(
                        convert_preprocessed, crs=crs, folder='IMG_' + id_glacier, scale=30)
    
            # ------------------ EXPORT CLASSIFICATION MAPS ------------------ #
            if export_condition["FACIES_MAP"] == "Y":
                print("Exporting classification maps...")
                if export_condition["Directory"] == "Local":
                    write_to_local(response=convert_collection, path=path_clas)
                    # Optional: Export each band separately
                    geemap.ee_export_image_collection(
                        convert_collection, out_dir=path_clas,
                        scale=30, crs=crs, file_per_band=True)
                elif export_condition["Directory"] == "Drive":
                    geemap.ee_export_image_collection_to_drive(
                        map_collection, folder='FACIES_MAP_' + id_glacier, scale=30)
    
            # ------------------ EXPORT METRICS TABLE ------------------ #
            if export_condition["TABLES"] == "Y":
                print("Exporting facies table...")
                facies_csv_name = f"{id_glacier}_{start_year.getInfo()}_{end_year.getInfo()}_{doy_start.getInfo()}_{doy_end.getInfo()}_metrics.csv"
                file_csv = os.path.join(path_clas, facies_csv_name)
    
                if export_condition["Directory"] == "Local":
                    write_sla_data(sla_collection=metrics_data, file=file_csv)
                elif export_condition["Directory"] == "Drive":
                    write_sla_dataDrive(
                        sla_collection=metrics_data,
                        file="TABLES_" + id_glacier,
                        filename=facies_csv_name)
    
            print("Export complete.\n")
    
        index += 1
    
    # End of processing
    end = time.time()
    print("All Done...!")
    print(f"It took {end - start:.2f} seconds")


if __name__ == "__main__":
    main()