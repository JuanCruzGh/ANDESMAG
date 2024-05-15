# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 18:58:04 2022

@author: lcsru
"""
import ee


def get_albedo_data(region,scale):

  image = ee.Image();
  date = ee.Date(image.get('system:time_start'));

  mean_a = image.reduceRegion(**{
    'reducer': ee.Reducer.mean(),
    'geometry': region.geometry(),
    'scale': scale,
    'maxPixels': 1e9
    });
  
  std_a = image.reduceRegion(**{
    'reducer':ee.Reducer.stdDev(),
    'geometry': region.geometry(),
    'scale': scale,
    'maxPixels': 1e9
    });
  max_a = image.reduceRegion(**{
    'reducer':ee.Reducer.max(),
    'geometry': region.geometry(),
    'scale': scale,
    'maxPixels': 1e9
    });
  

  min_a = image.reduceRegion(**{
    'reducer':ee.Reducer.min(),
    'geometry': region.geometry(),
    'scale': scale,
    'maxPixels': 1e9
    });

  
  # y devuelve una característica con geometría 'null' con propiedades (dictionary)  
  
  stats = ({'mean_albedo': mean_a.get('albedo'),
                            'std_albedo':std_a.get('albedo'),
                            'max_albedo':max_a.get('albedo'),
                            'min_albedo':min_a.get('albedo'),
                            'date': date,
           });
    
  """
  stats = ({'mean_albedo': mean_a,
                            'std_albedo':std_a,
                            'max_albedo':max_a,
                            'min_albedo':min_a,
                            'date': date,
           });
   """  
  return mean_a
