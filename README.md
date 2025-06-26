
# ANDESMAG
##  Andean Automated Surface Mapping on Glaciers
---

## Introduction

This tutorial presents the usage of **ANDESMAG**, a glacier facies classification algorithm written in Python. It leverages the Google Earth Engine API and requires an active account.

The algorithm processes optical imagery (e.g., Landsat, Sentinel) to classify glacier surface facies such as **snow**, **ice**, **debris**, and **water**.

From these classified images, various glacier monitoring metrics are extracted, including:
* **SLA** (Snow Line Altitude)
* **SCA** (Snow Cover Area)
* **DEE** (Debris Emergence Elevation)
* **DCA** (Debris Covered Area)
- and others.

These results are exported as CSV tables for further analysis.

---

## Workflow Overview

The general workflow consists of:

1. Installing dependencies
2. Configuring input parameters
3. Running the processing script
4. Visualizing results

---



## Installing Dependencies

### Recommended (with Mamba):

mamba install -c conda-forge geemap
mamba install -c conda-forge earthengine-api


Alternatively (with pip):

pip install geemap
pip install earthengine-api

---

## Initial Configuration
### Edit the config.py file with the following parameters:

- asset: Path to the glacier polygon dataset in your Earth Engine assets. Ensure the glacier ID field is named "ID_local" for the 'ngi_arg' branch or "rgi_id" for 'rgi_v7'.
- id_glacier_list: List of glacier IDs to process, matching exactly the IDs in the asset.
- crs: Output projection (e.g., "EPSG:4326").
- batch: List of tuples indicating the year range for processing.
- doy_start, doy_end: Day of year range for image selection.
- cloudiness: Maximum allowed cloud coverage in percent.
- coverage: Minimum scene coverage (percent) over the glacier polygon.
- hsboolean: Boolean (1=True, 0=False) for applying hillshade masking.
- dem: Digital elevation model to use ("SRTM" or "ALOS").

#### Example:
- asset = ee.FeatureCollection("projects/facies-mapping/assets/RGI7-SA-C17")
- id_glacier_list = ["RGI2000-v7.0-C-17-21353"]
- crs = "EPSG:4326"
- batch = [(2019, 2019)]
- doy_start = ee.Number(360)
- doy_end = ee.Number(365)
- cloudiness = ee.Number(50)
- coverage = 80
- hsboolean = 0
- dem = "SRTM"

### Export Settings
#### These are controlled via export_condition:

| Parameter    | Description                              |
| ------------ | ---------------------------------------- |
| `Directory`  | `"Drive"` or `"Local"`                   |
| `TABLES`     | `"Y"` to export metrics as CSV           |
| `IMG`        | `"Y"` to export input base images        |
| `FACIES_MAP` | `"Y"` to export classified facies images |

And specify local output paths:

- dir_facies – directory for classified images

- dir_tables – directory for metric tables

- dir_img – directory for input imagery

⚠️ Local export is significantly slower than exporting to Google Drive.

#### Example
export_condition = {
    "Directory": "Local",
    "TABLES": "Y",
    "IMG": "Y",
    "FACIES_MAP": "Y"
}

dir_facies = "./test_facies_rgi"
dir_tables = "./test_tables_rgi"
dir_img = "./test_img_rgi"

---

## Running the Script

### Run main.py in your terminal. Based on your configuration, it will output:

Several base images (e.g., 20191227T143656_T19HDD.tif)

Corresponding classified facies maps

One metrics table (e.g., RGI2000-v7.0-C-17-21353_2019_2019_360_365_metrics.csv)

---

## Visualizing Results
#### Run view_results.py to display:

1) The input image

2) The facies-classified image

3) A plot of extracted metrics:

* SLA (Snow Line Altitude)

* SCA (Snow Cover Area)

* DEE (Debris Emergence Elevation)

* DCA (Debris Covered Area)

<p align="center">
  <img width="337" alt="example_ANDESMAG" src="https://github.com/user-attachments/assets/b978bb78-34b0-4cab-98b5-f88cdcd20a1b" />
</p>


## Classification Categories

| Number | Class              |
| ------ | ------------------ |
| 0      | Ice                |
| 1      | Snow               |
| 2      | Water              |
| 3      | Debris Cover       |
| 4      | Clouds             |
| 6      | Shadow on Snow     |
| 8      | Unspecified Shadow |

---

## References

*Ghilardi Truffa et al. (in prep.)
Evolution of debris-covered glaciers in the Central Andes of Argentina: trends over the past four decades.*

*Zeller, J. (2020)
Automated classification of supraglacial surface facies for snow line altitude monitoring using Google Earth Engine.*

*Rastner, P. et al. (2019)
On the Automated Mapping of Snow Cover on Glaciers and Calculation of Snow Line Altitudes from Multi-Temporal Landsat Data.
Remote Sensing 11(12), 1410. https://doi.org/10.3390/rs11121410*
