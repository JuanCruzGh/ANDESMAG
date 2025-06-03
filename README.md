
<div align="center">
# ANDESMAG
##  Andean Automated Surface Mapping on Glaciers

In this version, multiple parameters can be modified directly from the main code, including the classification thresholds. The script is also structured to efficiently run on a list of glaciers (based on ID) across multiple years. A Google Earth Engine account is required, and the working polygons must be stored as an asset, as they are needed as input for the algorithm.
The algorithm allows exporting three types of outputs:

1)  Raw images (.tif),
  
2)  Classified images (.tif), and
   
3)  Tables containing the metrics derived from each image (.csv).

These outputs can be exported either to Google Drive or to a local directory, as defined by the user in the main code.

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

*Tutorial in progress ...*

## References:

*Ghilardi Truffa et al (in prep)* Evolution of debris-covered glaciers in the Central Andes of Argentina: trends over the past four decades.

*Zeller J (2020)* Automated classiﬁcation of supraglacial surface facies for snow line altitude monitoring using the Google Earth Engine. https://lean-gate.geo.uzh.ch/typo3conf/ext/qfq/Classes/Api/download.php/mastersThesis/752

*Rastner P and others (2019)* On the Automated Mapping of Snow Cover on Glaciers and Calculation of Snow Line Altitudes from Multi-Temporal Landsat Data. Remote Sensing 11(12), 1410. doi:10.3390/rs11121410.
