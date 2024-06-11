# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 18:58:04 2022

@author: lcsru
"""
import ee
import geemap

def get_vector(image,region):
# Define arbitrary thresholds on the 6-bit nightlights image.
   zones = image.lt(1)
   zones = zones.updateMask(zones.neq(0))

# Convert the zones of the thresholded nightlights to vectors.
   vectors = zones.addBands(image).reduceToVectors(**{
  'geometry': region,
  'crs': image.projection(),
  'scale': 1000,
  'geometryType': 'polygon',
  'eightConnected': False,
  'labelProperty': 'zone',
  'reducer': ee.Reducer.mean()
   })
   return vectors


