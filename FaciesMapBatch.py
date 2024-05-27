"""
    Main code to process, make the facies map, and extract the SLA (snow Line Altitude)
    for glacier larger than 0.1 k2 from the National Glacier Inventory of Argentina.
    """

# Importing external modules
# importing earth engine module
import ee

# importing geemap module
import geemap
# importing geopandas
import geopandas as gpd
# Import pandas
import pandas as pd
# importing os module
import os
# importing logging module
import logging
# importing time module
import time
# import json module
import json

# Me autentico una sola vez antes de correr despues lo silencio
ee.Authenticate()

# Intialize Google Earth Engine API
ee.Initialize()

# Import the ad-hoc modules to create the facies maps and extract the SLA
# from sla.prep_final32 import PreProcessor  # noqa
from sla.prep_final_jcgtV1 import PreProcessor  # noqa
from sla.cloud_shadow_mask import add_cloud_shadow  # noqa
from sla.hill_shadow import add_hill_shadow  # noqa
from sla.classifier import decision_tree  # noqa
from sla.main_patches_debris import extract_sla_patch  # noqa
from sla.delete_duplicate import no_duplicate


#%% BATCH 01
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
    



# Define parent Directory path to save the facies maps (one folder per glacier)
parent_facies = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/DebrisCoverGlacier_Scrips/sla-sca-master/test_22_04_2024/processed"

# Define parent Directory path to save the preprocessed images (one folder per glacier)
parent_prep = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/DebrisCoverGlacier_Scrips/sla-sca-master/test_22_04_2024/preprocessed"

##################################################################################

# Running the script



logger = logging.getLogger(__name__)

start = time.time()

print("starting...")

##############################################################################
""" 
Define the searching parameters
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

dem: Digital Elevation DEM used to calculate the hill shade and the SLA.

"""

# Glacier list

ing_list = ["G700681O326355S"] # horcones sup
# ing_list = ["G700069O329897S"] # buena img

# Defino los batch en que voy a partir la descarga; la idea es que sean
# tuplas con los años de inicio y años de fin
batch = [(2022, 2022)] #lista de tuplas

# start_year = ee.Number(1985)
# end_year = ee.Number(2010)
doy_start = ee.Number(100) 
doy_end = ee.Number(110)
cloudiness = ee.Number(50)
coverage = 50
hsboolean = 0
hs_start = doy_start
hs_end = doy_end
dem = "SRTM"

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
        )
        print("preprocessing...")
        preprocessed = preprocessor.execute()
        list_prep1 = ee.List(preprocessed.aggregate_array('system:time_start'))
    
        # Detectar duplicador
        preprocessed = no_duplicate(image_collection=preprocessed)
        list_prep2 = ee.List(preprocessed.aggregate_array('system:time_start'))
        
        # Running the shadow mask module
        print("processing cloud shadow mask...")
        preprocessed = preprocessed.map(add_cloud_shadow)
    
        # Running the hill shadow correction module
        print("processing hill shadow...")
        preprocessed = add_hill_shadow(image_collection=preprocessed, hs_start=hs_start, hs_end=hs_end)
        
        
        # Running the Classifier module
        print("initiating classifier...")
        map_collection = preprocessed.map(decision_tree)
        
        
        # Running the SLA module
        print("initiating SLA extraction...")
        SLA_collection = map_collection.map(extract_sla_patch)
        # convert to feature collection
        SLA_data = ee.FeatureCollection(SLA_collection) 
    
        # Save the results to the local driver
        print("writing to local...")
    
        # Create the paths
        path_clas = os.path.join(parent_facies, ing_id)
        path_prep = os.path.join(parent_prep, ing_id)
        
        # Check if the path already exist
        try:
            os.mkdir(path_clas)
        except FileExistsError:
            pass
        try:
            os.mkdir(path_prep)
        except FileExistsError:
            pass
            
    
        # Change Facies map collection to int8 to export
        # convert_collection = map_collection.map(ee.Image.int8) 
        
        # WRITE LOCAL   
        # Write preprocessed images to local drive (usando la función write_to_local)
        # write_to_local(response=preprocessed, path = path_prep)
       
        # Write facies maps to local drive (usando la función write_to_local)
        # write_to_local(response=convert_collection, path = path_clas)
        
        
        
        # Write facies maps to local drive usando la función nativa de geemap
        #geemap.ee_export_image_collection(convert_collection, out_dir=path_clas, scale=30,  crs='EPSG:4326', file_per_band=True)
       
        # Write facies maps to Google DRIVE (USAR CUANDO LAS IMAGENES SON MUY GRANDES)
        # geemap.ee_export_image_collection_to_drive(map_collection, folder='export_GPM_facies', scale=30)
        
        # Write Preprocessed images to Google DRIVE  (USAR CUANDO LAS IMAGENES SON MUY GRANDES) 
        # geemap.ee_export_image_collection_to_drive(preprocessed, folder='export_GPM_prep', scale=30)
        
        
        print("writing map")
         
        # create filename for the SLA data (csv and json)
        sla_csv_name = [str(start_year.getInfo()),'_', str(end_year.getInfo()),'_',str(doy_start.getInfo()),'_',str(doy_end.getInfo()),'_sla.csv']
        sla_csv_name = ''.join(sla_csv_name)
        
        # agrego el ID_local del glaciar para exportar a Drive
        sla_csv_name_DRIVE = ing_id + "_" + sla_csv_name[:-8]
        
        # sla_json_name = [str(start_year.getInfo()),'_',str(doy_start.getInfo()),'_',str(doy_end.getInfo()),'_sla.json']
        # sla_json_name = ''.join(sla_json_name)
        
        # path and name of the csv and json file where the SLA data will be writed
        file_csv = os.path.join(path_clas,sla_csv_name)       
        
        # file_json = os.path.join(path_clas,sla_json_name)
       
        
        # Save SLA data as csv to local drive
        # write_sla_data(sla_collection = SLA_data, file= file_csv)
       
        # print("writing csv")
        
        
        # Save SLA data as csv to Google drive
        write_sla_dataDrive(sla_collection=SLA_data, file="PYTHON_RUN_FaciesMapBatch", 
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
