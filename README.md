# Glacier Facies Algorithm versión jcgt_V2 (threshold_fixed)
Automated classification algorithm of glacial facies based on Zeller (2020) GEE version. In this version (jcgtV2) you can modify the classification thresholds directly in the main code (FaciesMapBatch_jcgtV2.py). Also the input of DEMs and the asset with glacier boundaries are in the main code. 

**Asset INPUT: It is important that the input asset provided to the code contains an attribute called 'ID_local' in its attribute table, where each glacier's ID is listed.**

FaciesMapBatch_jcgtV2 its the main code.

*Aclaration: main_patches_debris_jcgtV4 is the new module that fixes the problem with the output ‘{AVS_DSM: xxx_number_xxx}’ in both the debris emergence altitude and standard deviations (SLA and DEA).*
