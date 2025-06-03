
# ANDESMAG: Andean Automated Surface Mapping on Glaciers

Automated classification algorithm of glacial facies based on ASMAG Algorithm (Rastrner and others, 2019; Zeller, 2020). In this version (jcgtV2) you can modify the classification thresholds directly in the main code (FaciesMapBatch_jcgtV2.py). Also the input of DEMs and the asset with glacier boundaries are in the main code.

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

*How to use: ... still working on ...*

*References:*

*Ghilardi Truffa et al (in prep)*

*Zeller J (2020)* Automated classiﬁcation of supraglacial surface facies for snow line altitude monitoring using the Google Earth Engine. https://lean-gate.geo.uzh.ch/typo3conf/ext/qfq/Classes/Api/download.php/mastersThesis/752

*Rastner P and others (2019)* On the Automated Mapping of Snow Cover on Glaciers and Calculation of Snow Line Altitudes from Multi-Temporal Landsat Data. Remote Sensing 11(12), 1410. doi:10.3390/rs11121410.
