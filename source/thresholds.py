# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 16:55:42 2025

@author: ThinkPad
"""

# source/thresholds.py

# ----------------------- SET THRESHOLDS -------------------------------------#

THRESHOLD_CLOUD_SCORE = [
    0.1,  # 0 = Clouds are reasonably bright in the blue band [MIN]
    0.3,  # 1 = Clouds are reasonably bright in the blue band [MAX]
    0.2,  # 2 = Clouds are reasonably bright in all visible bands [MIN]
    0.8,  # 3 = Clouds are reasonably bright in all visible bands [MAX]
    0.3,  # 4 = Clouds are reasonably bright in all infrared bands [MIN]
    0.8,  # 5 = Clouds are reasonably bright in all infrared bands [MAX]
    0.7,  # 6 = However, clouds are not snow [MIN]
    0.6,  # 7 = However, clouds are not snow [MAX]
    0.7   # 8 = Cloud score per pixel
]

THRESHOLD_ADD_CLOUD_SCORE = [
    0.1,   # 0 = BLUE BAND [MIN]
    0.5,   # 1 = BLUE BAND [MAX]
    0.2,   # 2 = RGB COMBINATION [MIN]
    0.8,   # 3 = RGB COMBINATION [MAX]
    -0.1,  # 4 = NDMI [MIN]
    0.1,   # 5 = NDMI [MAX]
    0.4,   # 6 = NDSI [MIN]
    0.1    # 7 = NDSI [MAX]
]

THRESHOLD_ADD_CLOUD_SHADOW = [
    20,    # 0 = CLOUD THRESHOLD
    0.45   # 1 = INFRARED THRESHOLD
]

THRESHOLD_DECISION_TREE = [
    0.5,  # 0 = Shadow Score [MIN]
    2,    # 1 = Shadow Score [MAX]
    0.8,  # 2 = Snow shadow mask or Unknown shadow
    0.6,  # 3 = Water or Not Water
    0.1,  # 4 = Shadow on water
    0.4,  # 5 = Snow/Ice or Cloud/Debris
    0.45, # 6 = NIR Threshold for Snow mask [MIN]
    0.54, # 7 = NIR Threshold for Snow mask [MAX]
    0.47, # 8 = Fixed Threshold [otsu]
    0.5,  # 9 = Rescale Ice vs Snow difference [MIN]
    2,    # 10 = Rescale Ice vs Snow difference [MAX]
    0.7,  # 11 = Ice
    0.6,  # 12 = Clouds
    0.3   # 13 = Debris
]
