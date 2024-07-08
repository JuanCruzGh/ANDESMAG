<div align="center">
  <img src="https://github.com/JuanCruzGh/GlacierFaciesAlgorithm/assets/87556377/7c69e04e-97b1-4d16-9121-0cc746739e28" alt="image">
</div>

# Glacier Facies Algorithm 
Automated classification algorithm of glacial facies based on Zeller (2020) GEE version. In this version (jcgtV2) you can modify the classification thresholds directly in the main code (FaciesMapBatch_jcgtV2.py). Also the input of DEMs and the asset with glacier boundaries are in the main code. 

**Asset INPUT: It is important that the input asset provided to the code contains an attribute called 'ID_local' in its attribute table, where each glacier's ID is listed.**

References of the output classification categories:
<div align="center">

| Number | Class              |
|--------|--------------------|
| 0      | Ice                |
| 1      | Snow               |
| 2      | Water              |
| 3      | Debris Cover       |
| 4      | Clouds             |
| 6      | Shadow on Snow     |
| 8      | Unspecified Shadow |

</div>

FaciesMapBatch_jcgtV2 its the main code.

*Aclaration: main_patches_debris_jcgtV4 is the new module that fixes the problem with the output ‘{AVS_DSM: xxx_number_xxx}’ in both the debris emergence altitude and standard deviations (SLA and DEA).*
