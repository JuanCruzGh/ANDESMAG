
![algorithm example2](https://github.com/user-attachments/assets/d11834dd-23bd-48d8-928c-9268bb65f417)
# Glacier Facies Algorithm 

Automated classification algorithm of glacial facies based on Zeller (2020) GEE version. In this version (jcgtV2) you can modify the classification thresholds directly in the main code (FaciesMapBatch_jcgtV2.py). Also the input of DEMs and the asset with glacier boundaries are in the main code. FaciesMapBatch_jcgtV2 its the main code.

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

*Aclaration: main_patches_debris_jcgtV5 is the new module that fixes the problem with the output ‘{AVS_DSM: xxx_number_xxx}’ in both the debris emergence altitude and standard deviations (SLA and DEA).*

*Link to Zeller (2020): https://lean-gate.geo.uzh.ch/typo3conf/ext/qfq/Classes/Api/download.php/mastersThesis/752*
