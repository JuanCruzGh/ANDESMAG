# Glacier Facies Algorithm versión jcgt_V2 (threshold_fixed)
Automated classification algorithm of glacial facies based on Zeller (2020) GEE version. In this version (jcgtV2) you can modify the classification thresholds directly in the main code.
Also the input of DEMs and the asset with glacier boundaries are in the main code. 

FaciesMapBatch its the main code

Issues to improve:

* sTD Debris Emergence Altitude (stdDev DEA, 0 means no touch between Main patches [m]) doesn't works

* Some cases in Snow Line Altitude-msnm or Debris Emergency Altitude-msnm the output is something like "{AVE_DSM=4957}"; must be "4957"
