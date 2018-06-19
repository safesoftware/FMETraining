
Here are the scenarios:

Scenario|Problem
--|--
Business intelligence|You are a healthcare administrator with patient records describing length of hospital stay and other attributes. You also have data on the postcode where the patients live. Integrate this data with StatsCan demographic data to examine links between demographics, geography, and length of hospital stay. Produce a map and a chart or table showing your results.
City Government|The federal government has just announced a subsidy for building electric vehicle charging stations. The City of Vancouver Planning department has been tasked with identifying suitable locations for the stations. The city has money to build 4 stations; they must be on city-owned property; they must be near areas of high population density; they must be located near major intersections; and they must be spread out evenly. Integrate data to propose four locations.
Web-based data|You have developed a new application that generates a GeoJSON of recent killer whale sightings off the coast of Vancouver. However, you don't want a blank basemap under your data. Use FME to add some more data to your map and use it to find correlations with whale sightings. **Note:** this scenario lends itself to using [FME Server](https://www.safe.com/fme/fme-server/) for reading and writing data live. You can try to use this software if you have it available. Otherwise you can construct a workspace that generates a static map.


More data is available from the [City of Vancouver Open Data catalogue](http://data.vancouver.ca/datacatalogue/index.htm).

Topic|Format|Location (FMEData2018\Data\...)|
--|--|--
Addresses|Esri Geodatabase|Addresses\Addresses.gdb
Building Footprints|SpatialLite Database or AutoCAD DWG|Engineering\BuildingFootprints\building_footprints.sl3 or C:\FMEData2018\Data\Parcels\BuildingFootprints.dwg
Bike Paths|Esri Shapefile|Transportation\Cycling\BikePaths*.shp|
Business Licenses|Excel Spreadsheet|Planning\BusinessLicenses.xlsx
City Grid|Geography Markup Language|Boundaries\CityGrid.gml
City-owned Properties|Esri Shapefile|Parcels\CityProperties\CityProperties.shp
Coastal Zones|Geography Markup Language|Boundaries\CoastalZones\CoastalZones.gml
Community Resources|Esri Geodatabase|CommunityMapping\CommunityMap.gdb
Crime|Comma Separated Values|Emergency\Crime.csv
Drinking Fountains|Comma-separated Values|Engineering\DrinkingFountains.csv
Election Results|Excel Spreadsheet|Elections\ElectionResults.xls
Election Voting Districts|Geography Markup Language|Elections\ElectionVoting.gml
Elevation|Digital Elevation Model|ElevationModel\DEM-Full.dem
Firehalls with Zones|Geography Markup Language|Emergency\FireHallsWithZones.gml
Forward Sortation Areas (for postcode)|Esri Shapefile|Addresses\ForwardSortationAreas.shp
Land Boundary|Esri Shapefile|Boundaries\LandBoundary\VancouverLandBoundary.shp
Neighborhoods|Google Keyhole Markup Language|Boundaries\VancouverNeighborhoods.kml
Orthophotos (scale corrected aerial photographs)|TIFF|Orthophotos\*.tif
Parcels|AutoCAD DWG|Parcels\Parcels.dwg
Parking Meters|MapInfo TAB|Transportation\Parking\Meters.tab
Parking Tickets|Comma-separated Values|Transportation\Parking\ParkingTickets.csv
Parks|MapInfo TAB|Parks\Parks.tab
Planning Restrictions (Business Improvement Areas, Historic Areas, Noise Control Areas, and View Cones)|OCG Geopackage|Planning\PlanningRestrictions.gpkg
Point Cloud (LiDAR)|LAS|PointClouds\CoV*.laz
Public Art|Excel Spreadsheet|Culture\PublicArt.xlsx
Public Trees|Comma-separated Values|Parks\Parks.tab
Roads|AutoCAD DWG or Microstation DGN|Transportation\CompleteRoads.dwg or RoadsDGN.dgn
Street Lighting|AutoCAD DWG and Microstation DGN|Engineering\StreetLighting.dwg and StreetLightingDGN.dgn
Traffic Signals|AutoCAD DWG and Microstation DGN|Engineering\TrafficSignals.dwg and TrafficSignalsDGN.dgn
Zoning|MapInfo TAB|Zoning\Zones.tab
Zoning Descriptions|Adobe PDF|Zoning\ZoneDescriptions.pdf
