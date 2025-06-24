# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 18:28:37 2025

@author: ThinkPad
"""

"""
Configuration file for glacier facies mapping and SLA/DEA extraction.
This file centralizes all the user-defined parameters.
"""

import ee

# --------------------------- ASSETS & GLACIER LIST ---------------------------#

# FeatureCollection containing the glacier polygons to be analyzed.
# Must include a column "rgi_id" to match glacier IDs in id_glacier_list.

asset = ee.FeatureCollection(
    "projects/facies-mapping/assets/RGI7-SA-C17"
    )

# List of glacier IDs to be processed. Must match "rgi_id" values in ING.
id_glacier_list = ["RGI2000-v7.0-C-17-19589"] #Horcones superior glacier

# --------------------------- PROYECTION PARAMETERS -----------------------------#
crs = "EPSG:4326"
# scale = 30  # or 10 Sentinel only

# --------------------------- TEMPORAL PARAMETERS -----------------------------#

# List of (start_year, end_year) tuples for processing in yearly batches.
batch = [(2019, 2019)] 
        

# Day of year (DOY) range for filtering optical imagery (inclusive).
doy_start = ee.Number(345)  
doy_end = ee.Number(365)    


# Hillshade DOY range (usually same as image DOY).
hs_start = doy_start
hs_end = doy_end

# --------------------------- FILTERING THRESHOLDS ----------------------------#

# Maximum allowed cloudiness percentage over the glacier area.
cloudiness = ee.Number(50)  # percent

# Minimum required image coverage over the glacier polygon.
coverage = 80  # percent

# Whether or not to apply hillshade masking.
# 0 = False (no masking), 1 = True (apply masking)
hsboolean = 0

# Digital Elevation Model (DEM) to use for SLA and hillshade.
# Options: "SRTM" or "ALOS"
dem = "SRTM"

# --------------------------- EXPORT PARAMETERS -------------------------------#

# Export options for output data. Available options:
# Directory: "Drive" (default, faster) or "Local" (to disk)
# TABLES: "Y" or "N" – export facies metrics as CSV
# IMG: "Y" or "N" – export preprocessed satellite images
# FACIES_MAP: "Y" or "N" – export classified facies maps
export_condition = {
    "Directory": "Local",
    "TABLES": "Y",
    "IMG": "Y",
    "FACIES_MAP": "Y"
}

# --------------------- LOCAL EXPORT PATHS (IF NEEDED) ------------------------#

# Local directory to store classified facies maps and CSV metrics
parent_facies = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/GEO_facies"

# Local directory to store preprocessed image collections
parent_prep = "C:/Users/ThinkPad/OneDrive/IANIGLA/DebrisCoverGlaciers/GEO_img"
