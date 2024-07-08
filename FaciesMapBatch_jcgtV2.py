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
import geopandas as gpd
import pandas as pd
import os
import logging
import time
import json

# Only once!
# ee.Authenticate()

# Intialize Google Earth Engine API
ee.Initialize()

# --------------------------- INTERNAL MODULES -------------------------------#
from sla.prep_final_jcgtV2 import PreProcessor  # ADAPT (!); TR (!)
from sla.cloud_shadow_mask_jcgtV2 import add_cloud_shadow  # ADAPT (!); TR (!)
from sla.hill_shadow_jcgtV2 import add_hill_shadow # ADAPT (!); TR(!)
from sla.classifier_jcgtV2 import decision_tree  # ADAPT (!); TR (!)
from sla.main_patches_debris_jcgtV6 import extract_sla_patch  # ADAPT (!); TR(!)
from sla.delete_duplicate_jcgtV2 import no_duplicate # ADAPT (!); TR(!)

#%% 
# ------------------------------- FUNCTIONS ---------------------------------#

# Define a function to export the Facies maps as tiff files.
# We use it to save the facies map to the local server.
def write_to_local(response, path):
    """
    Writes a GEE object to the local filesystem in tiff format.
    Be cautious as this method will call the getInfo() method on the GEE
    object to retrieve all the results from the EE server.
    So it can be computationally expensive and block all further execution.
    """
    geemap.ee_export_image_collection(response, out_dir=path, scale=30,  crs='EPSG:4326')

    print(f"Results written to {path}")


# Define a function to save the SLA data as csv
def write_sla_data(sla_collection, file):
    """
    Writes a SLA data (feature Collection) to the local filesystem in CVS
    But we really need is to join the latest date to a file
    """
    geemap.ee_to_csv(sla_collection, file)

    #print(f"SLA data written to {file}")

# Define a function to save the SLA data as csv in Google Drive

def write_sla_dataDrive(sla_collection, file, filename):
    """
    Writes a SLA data (feature Collection) to the Google Drive in CVS
    """
    # task = ee.batch.Export.table.toDrive(
    geemap.ee_export_vector_to_drive(collection=sla_collection,
                                        description= filename,
                                        folder=file,
                                        fileFormat='CSV',
                                        )

    # task.start()


# Define a function to save the SLA data as json
def write_to_json(response, filename):
    """
    Writes a GEE object to the local filesystem in JSON format.

    Be cautious as this method will call the getInfo() method on the GEE
    object to retrieve all the results from the EE server.
    So it can be computationally expensive and block all further execution.
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps(response.getInfo()))

    #print(f"Results written to {filename}")
    
def convert_to_float(image):
    return image.toFloat()


# ----------------------- SET THRESHOLDS -------------------------------------#

THRESHOLD_CLOUD_SCORE = [

        0.1,  # 0 = Clouds are reasonably bright in the blue band [MIN]
        0.3,  # 1 = Clouds are reasonably bright in the blue band [MAX]
        
        0.2,    # 2 = Clouds are reasonably bright in all visible bands [MIN]
        0.8,    # 3 = Clouds are reasonably bright in all visible bands [MAX]
        
        0.3, # 4 = Clouds are reasonably bright in all infrared bands [MIN]
        0.8,  # 5 = Clouds are reasonably bright in all infrared bands [MAX]
        
        0.7, # 6 = However, clouds are not snow [MIN]
        0.6, # 7 = However, clouds are not snow [MAX]
        
        0.7, # 8 = add band with cloud score per pixel and select cloud pixels to mask original image
]


THRESHOLD_ADD_CLOUD_SCORE = [
    
    0.1, # 0 = BLUE BAND [MIN]
    0.5, # 1 = BLUE BAND [MAX]
    
    0.2, # 2 = RGB COMBINATION [MIN]
    0.8, # 3 = RGB COMBINATION [MAX]
    
    
    -0.1, # 4 = NDMI [MIN]
    0.1, # 5 = NDMI [MAX]
    
    0.4, # 6 = NDSI [MIN]
    0.1 # 7 = NDSI [MAX]
    
    ]

THRESHOLD_ADD_CLOUD_SHADOW = [
    
    20, # 0 = CLOUD THRESHOLD
    0.45, # 1 = INFRARED THRESHOLD
    
    ]

THRESHOLD_DECISION_TREE = [
    
    0.5, # 0 = Shadow Score [MIN] / Constant?
    2, # 1 = Shadow Score [MAX] / Constant?

    0.8, # 2 = Threshold Snow shadow mask or Unknown shadow
    0.6, # 3 = Threshold for Water or Not Water
    0.1, # 4 = Threshold for Shadow on water
    0.4, # 5 = Threshold for Snow/Ice or Clud/Debris
    
    0.41, # 6 = NIR Threshold for Snow mask [MIN]
    0.54, # 7 = NIR Threshold for Snow mask [MAX]
    
    0.47, # 8 = Fixed Threshold [otsu]
    
    0.5, # 9 = Rescale Ice vs Snow difference [MIN] / Constant?
    2, # 10 = Rescale Ice vs Snow difference [MAX] / Constant?
    
    0.7, # 11 = Threshold for Ice
    0.6, # 12 = Threshold for Clouds
    0.3, # 13 = Threshold for Debris
    ]

# ----------------------- SET PARAMETERS -------------------------------------#

# Running the script

logger = logging.getLogger(__name__)

start = time.time()

print("starting...")

##############################################################################
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

# ONLY FOR THE LOCAL DIRECTORY DOWNLOAD!
# Define parent Directory path to save the facies maps (one folder per glacier)
# parent_facies = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/DebrisCoverGlacier_Scrips/sla-sca-master/test_22_04_2024/processed"

# Define parent Directory path to save the preprocessed images (one folder per glacier)
# parent_prep = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/DebrisCoverGlacier_Scrips/sla-sca-master/test_22_04_2024/preprocessed"

# DEM SRTM y ALOS; ADAPT (!)
SRTM = ee.Image("USGS/SRTMGL1_003")
ALOS = ee.Image("JAXA/ALOS/AW3D30/V2_2")

# Asset whit polygons; ADAPT (!)
ING = ee.FeatureCollection(
    "users/lcsruiz/Mapping_seasonal_glacier_melt_across_the_ANDES_with_SAR/Glaciares_Arg_Andes_dissolve"
    )

# Glacier list
ing_list = ["G700681O326355S"] # horcones sup
batch = [(1995, 1999)]
         # (2000, 2003),
         # (2024, 2024)] # [(start_year, end_year)]
doy_start = ee.Number(100) 
doy_end = ee.Number(110)
cloudiness = ee.Number(50)
coverage = 50
hsboolean = 0
hs_start = doy_start
hs_end = doy_end
dem = "SRTM" # choose dem

# Starting the loop through the ing_list
index = 0

while index < len(ing_list):
    for i in range(len(batch)):
        
        # Redefino el año de inicio y de fin por lote
        start_year = ee.Number(batch[i][0])
        end_year = ee.Number(batch[i][1])
    
        ing_id = ing_list[index]
        # Running the preproces module
        preprocessor = PreProcessor(
            ing_id=ing_id,
            start_year=start_year,
            end_year=end_year,
            doy_start=doy_start,
            doy_end=doy_end,
            cloudiness=cloudiness,
            coverage=coverage,
            hsboolean=hsboolean,
            dem=dem,
            THRESHOLD_CLOUD_SCORE=THRESHOLD_CLOUD_SCORE # TR (!)
        )
        print("preprocessing...")
        preprocessed = preprocessor.execute(ING) # ADAPT (!)
        list_prep1 = ee.List(preprocessed.aggregate_array('system:time_start'))
    
        # Detectar duplicador
        preprocessed = no_duplicate(image_collection=preprocessed)
        list_prep2 = ee.List(preprocessed.aggregate_array('system:time_start'))
        
        # Running the shadow mask module
        print("processing cloud shadow mask...")
        preprocessed = preprocessed.map(lambda image: add_cloud_shadow(image, ING, 
                                                                       THRESHOLD_ADD_CLOUD_SHADOW, # TR (!)
                                                                       THRESHOLD_ADD_CLOUD_SCORE)) # TR (!)
    
        # Running the hill shadow correction module
        print("processing hill shadow...")
        preprocessed = add_hill_shadow(image_collection=preprocessed, hs_start=hs_start, hs_end=hs_end)
        
        
        # Running the Classifier module
        print("initiating classifier...")
        # map_collection = preprocessed.map(decision_tree())
        map_collection = preprocessed.map(lambda image: decision_tree(image, SRTM, ING, THRESHOLD_DECISION_TREE)) # ADAPT (!); TR (!)
    
        
        # Running the SLA module
        print("initiating SLA extraction...")
        SLA_collection = map_collection.map(lambda image:extract_sla_patch(image, SRTM, ALOS, ING)) # ADAPT (!)
        # convert to feature collection
        SLA_data = ee.FeatureCollection(SLA_collection) 
    
        # Save the results to the local driver
        # print("writing to local...")
    
        # Create the paths
        # path_clas = os.path.join(parent_facies, ing_id)
        # path_prep = os.path.join(parent_prep, ing_id)
        
        # # Check if the path already exist
        # try:
        #     os.mkdir(path_clas)
        # except FileExistsError:
        #     pass
        # try:
        #     os.mkdir(path_prep)
        # except FileExistsError:
        #     pass
            
    
        # Change Facies map collection to int8 to export
        # convert_collection = map_collection.map(ee.Image.int8) # NO HACE FALTA TRANSFORMAR; ADAPT (!)
        
        # Change Preprocessed image to float to export
        convert_preprocessed = preprocessed.map(convert_to_float) # ADAPT(!)
        
        # WRITE LOCAL   
        # Write preprocessed images to local drive (usando la función write_to_local)
        # write_to_local(response=preprocessed, path = path_prep)
       
        # Write facies maps to local drive (usando la función write_to_local)
        # write_to_local(response=convert_collection, path = path_clas)
        
        
        # Write facies maps to local drive usando la función nativa de geemap
        #geemap.ee_export_image_collection(convert_collection, out_dir=path_clas, scale=30,  crs='EPSG:4326', file_per_band=True)
       
        # Write facies maps to Google DRIVE (USAR CUANDO LAS IMAGENES SON MUY GRANDES)
        geemap.ee_export_image_collection_to_drive(map_collection, folder='Test_FaciesMapBatch_jcgtV1', scale=30)
        
        # Write Preprocessed images to Google DRIVE  (USAR CUANDO LAS IMAGENES SON MUY GRANDES) 
        # geemap.ee_export_image_collection_to_drive(preprocessed, folder='Test_FaciesMapBatch_jcgtV1', scale=30)
        geemap.ee_export_image_collection_to_drive(convert_preprocessed, folder='Test_FaciesMapBatch_jcgtV1', scale=30) #ADAPT (!)

        
        print("writing map")
         
        # create filename for the SLA data (csv and json)
        sla_csv_name = [str(start_year.getInfo()),'_', str(end_year.getInfo()),'_',str(doy_start.getInfo()),'_',str(doy_end.getInfo()),'_sla.csv']
        sla_csv_name = ''.join(sla_csv_name)
        
        # agrego el ID_local del glaciar para exportar a Drive
        sla_csv_name_DRIVE = ing_id + "_" + sla_csv_name[:-8]
        
        # sla_json_name = [str(start_year.getInfo()),'_',str(doy_start.getInfo()),'_',str(doy_end.getInfo()),'_sla.json']
        # sla_json_name = ''.join(sla_json_name)
        
        # path and name of the csv and json file where the SLA data will be writed
        # file_csv = os.path.join(path_clas,sla_csv_name)       
        
        # file_json = os.path.join(path_clas,sla_json_name)
       
        
        # Save SLA data as csv to local drive
        # write_sla_data(sla_collection = SLA_data, file= file_csv)
       
        # print("writing csv")
        
        
        # Save SLA data as csv to Google drive
        write_sla_dataDrive(sla_collection=SLA_data, file="FaciesMapBatch_jcgtV1", 
                            filename=sla_csv_name_DRIVE)
        
        print("writing csv Drive")
        
        # Save SLA data as json to local drive
       # write_to_json(response = SLA_data, filename= file_json)
        # print("writing json")
        
    
    index += 1

end = time.time()
print("All Done...!")
print(f"It took {end - start:.2f} seconds")

# End the loop for ech glacier
