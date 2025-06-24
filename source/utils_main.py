# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 16:48:37 2025

@author: ThinkPad
"""

import geemap
from source.config import crs

def write_to_local(response, path):
    """
    Export an Earth Engine image collection to local directory.
    """
    geemap.ee_export_image_collection(response, out_dir=path, scale=30, crs=crs)
    print(f"Results written to {path}")

def write_sla_data(sla_collection, file):
    """
    Export SLA feature collection to local CSV.
    """
    geemap.ee_to_csv(sla_collection, file)

def write_sla_dataDrive(sla_collection, file, filename):
    """
    Export SLA feature collection to Google Drive as CSV.
    """
    geemap.ee_export_vector_to_drive(
        collection=sla_collection,
        description=filename,
        folder=file,
        fileFormat='CSV',
    )

def convert_to_float(image):
    """
    Convert EE image to float.
    """
    return image.toFloat()
