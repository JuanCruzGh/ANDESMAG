
# A<sup>2</sup>MAG: Andes Automated Snow Mapping on Glaciers

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

*Results table are in (-link and doi pending-)*

*Link to Zeller (2020): https://lean-gate.geo.uzh.ch/typo3conf/ext/qfq/Classes/Api/download.php/mastersThesis/752*
