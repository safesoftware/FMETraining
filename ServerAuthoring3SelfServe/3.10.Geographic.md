# Geographic Selection

In most Self-Serve applications the user will need to be given a choice of geographic area of interest

Although most workspaces are designed around FME feature types, this may not be how the end-users see the data, or how they need to select it. An installation that provided selection only by layer (or even a group of layers) would be very limiting indeed.

Besides layers, other methods of data selection revolve around spatially defining an area of interest. There are three obvious ways of doing so:

- A simple, rectangular bounding box

- An existing area such as a regional or municipal boundary

- An ad-hoc area (one drawn by the user on the fly)

**Bounding Box**

A bounding box can be defined in several ways, but the easiest is to use a set of parameters.

All FME readers have parameters to define the bounding box (envelope) of data that is being read. This is the most efficient method of selecting an area of interest because it means FME does not have to read the entire dataset first and then clip it to size; it can read only what data is necessary. It’s particularly efficient if the source format has a spatial index, and it applies to both vector and raster datasets.

If these search envelope parameters are published, then the end-user is able to enter values that define the extent of the data he/she is interested in.

Besides the actual coordinates, there are two related parameters: “Clip to Search Envelope” and “Search Envelope Coordinate System”.

Clip to Search Envelope causes features that overlap the bounding box to be clipped and the outer part discarded. This will be the most common use for FME Server.

The Search Envelope Coordinate System means that the bounding box can have its own coordinate system, separate from the reader coordinate system. So the bounding box coordinates can be defined in a general coordinate system like Lat./Long, even if the data is UTM.

**Web Mapping and Bounding Boxes**

Bounding box parameters are particularly useful when a web mapping application (for example Google Earth) is requesting data. The application will provide the extents of the current map view and the workspace restricts itself to reading features within those extents.

This, of course, is done using published parameters. The parameters in the workspace need to be given specific names when published, as follows:

• bboxWest

• bboxEast

• bboxNorth

• bboxSouth

If given these names, both OGC services and the KML Network Link service can make use of these parameters. In fact, if you have used an OGC web service, or a KML Network Link service (as below), you might have noticed how these are used to pass information back to the workspace:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Using reader parameters like this ensures the data is reduced in size at
the earliest possible opportunity and so gives a better performance.”
</span>
</td>
</tr>
</table>

**Irregular Areas of Interest**

An irregularly shaped area cannot be used as a clip boundary in a Reader’s parameters.
However, it can be used to clip data using either a Clipper transformer or a FeatureReader transformer.

The Clipper has an input port for the area of interest (Clipper) and one for the main dataset (Clippee).

For example, here the portal will deliver only addresses that fall inside the boundary of the city of Vancouver:

Here is the same result but using a FeatureReader transformer.

The FeatureReader reads the main dataset directly, executing out one of any number of spatial filters.

In general the FeatureReader is a better choice than a Clipper when using a database with a spatial index, or when the spatial predicate is other than a simple CONTAINS function.

**Existing Area of Interest**

The main issue with an irregular area of interest is how to define that area. In some cases, the feature is already defined as a known shape, such as an administrative or municipal boundary, and already exists in a spatial dataset.

In that case the area can simply be read from the dataset and routed into the appropriate input port of the Clipper/FeatureReader transformer.

If the source contains a number of features, then a published parameter can be used for the enduser to identify the area they want and for FME to filter other features out.

For example, this Self-Serve workspace uses a Clipper transformer to deliver only addresses that fall within a chosen postal code. The postal code is selected by the user through a published parameter. The Tester transformer filters out postal code boundaries that don’t match the user’s selection.

**Ad Hoc Area of Interest**

In the case that the area of interest is not a previously known shape – for example it is one defined entirely by the end user – then a different technique is needed.

This scenario needs a published parameter through which a geometry string can be provided.
The geometry could be, for example, either WKT (Well-Known Text) or XML.

One simple method would be to use an AttributeCreator transformer and publish the Value part.

This could be used in a sequence like this, where the translation is triggered with a Creator, the geometry string retrieved with the AttributeCreator, the attribute contents converted into true geometry with a GeometryReplacer, and then the real data read with a FeatureReader:

To use XML you could also just publish the geometry parameter in a Creator transformer.

With these methods, a web mapping interface that allows the user to define their own custom area of interest can pass it to the FME workspace to be used as the area of interest in a Clipper or FeatureReader.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3F </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data
Download
Area
of
Interest</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Scenario</td>
<td style="border: 1px solid darkorange">Airphoto Data Vendor</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">GeoTiff Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Improve
the
data
download
service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Selection
of
data
via
geographic
area</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3f-­‐Begin-­‐
DataDownload.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3f-­‐Complete-­‐
DataDownload.fmw</td>
</tr>

</table>

The task here is to let the end user decide what area of data is to be delivered. For this exercise we’ll let them choose which neighborhood of the city they wish the data for.

**1. Start Workbench**

Start FME Workbench (if necessary). Open the workspace from Exercise 3e (or the start workspace for this exercise).

**2. Add Reader**

To filter by neighborhood we need to read a dataset of neighborhood boundaries.
Select Reader > Add Reader from the menubar and add a new Reader with the following parameters:

**Reader Forma**t Google Earth KML

**Reader Dataset** C:\FMEData2015\Data\Boundaries\VancouverNeighborhoods.kml

**Workflow Options** Individual Feature Types

When prompted to select feature types to add to the workspace, simply deselect everything except the Neighborhoods layer

**3. Add Reprojector**

Being a KML dataset, this data is in a latitude-longitude coordinate system and must therefore be reprojected to match the UTM coordinate system of the raster data.

Add a CsmapReprojector transformer to the workspace.

Connect it to the Neighborhood Reader feature type:

Open the transformer’s parameters dialog.

Leave the Source Coordinate System as <Read from feature> and set the Destination to UTM83-10.

**4. Add Parameter**

Now let’s add a custom parameter for the user to select which neighborhood to download.

Right-click on Published Parameters in the Navigator window and choose Add Parameter.
Add a parameter with the following settings:

Type Choice

Name AreaOfInterest

Prompt Select Neighborhood

Published Yes

Optional No

Start to configure the parameter by clicking the […] button for the Configuration parameter.

Instead of entering each neighborhood name separately, we’ll import a list of them from the KML
dataset. Start this process by clicking the Import button.

When prompted enter:

Reader Format Google Earth KML

Reader Dataset C:\FMEData2015\Data\Boundaries\VancouverNeighborhoods.kml

…and click Next. Select Neighborhoods as the Feature Type and click Next. Select
NeighborhoodName as the attribute to import from and click Next.

The dataset will now be scanned for valid values. When it is complete click Import.

We now have a list of available neighborhoods to choose from.

Notice that the names are already complete so we don’t need to use any sort of alias.

Click OK and OK again to close the parameter dialogs.

**5. Add Tester**

Now let’s add a Tester transformer. This will filter out the neighborhoods that weren’t selected.

Add a Tester and connect it to the CsmapReprojector transformer:

Open the Tester parameters dialog by clicking the red cog wheel button.

For the “Left Value” of the test, double-click in the field, click the drop-down arrow, and select Attribute Value > NeighborhoodName.
Set the

Tester operator to equals (=).

For the Right Value double-click in the field, click the drop-down arrow, then select User Parameter > AreaOfInterest.

Click OK to close the dialog.

**6. Add Clipper**

We now have a test to check where the neighborhood is the one chosen by the user, but we haven’t yet done anything with the result. We must use the chosen neighborhood as a boundary to clip the raster output.

Add a Clipper transformer.

Connect it up by connecting the Tester Passed port to the Clipper input port. Connect the VectorOnRasterOverlayer Raster port to the Clipper Clippee input port.

The Clipper:Inside port can be connected to the output feature type and any existing connector deleted. The workspace will now look like this:

**7. Delete Parameter**

As with the Roads data, the end-user does not need to see a parameter for the neighborhoods source, so locate the source Google Earth KML parameter and delete it.

**8. Test Run Workspace**

Save the workspace as Exercise3f.fmw Run the workspace using Run > Prompt and Run in FME Workbench.

For the source GeoTIFF files you’ll want to select all of the files to ensure the neighborhood is covered fully.

Then select a neighborhood to view the data; West End or Downtown are good to use.

**9. Publish to FME Server**

Save the workspace as Exercise3f.fmw.
Select File > Publish to FME Server from the menubar to start the publishing process.

Fill in the connection details and credentials as usual and then click Next to continue.

In the next dialog select Training as the repository to publish to and, as before, click on the button labelled Select Files.

Ensure that both the MicroStation roads dataset, and the KML neighborhoods dataset, are being uploaded to the repository, but that the Orthophotos are not.

Again, a warning message will alert you to the fact that the GeoTIFF files are being referenced
but not uploaded. Again, it’s fine to simply click OK to dismiss the dialog.

Register the workspace with the Data Download service again.

**10. Run Workspace on FME Server**

In the Web User Interface, run your workspace using the Data Download Service as if you are a user, as we have been doing in the previous exercises.

Notice the neighborhood is available as a dropdown list.

Pick a neighborhood – and enough source files to cover it – and run the workspace.

Congratulations: Your Data Download service now lets the end-user retrieve data within a set geographic area.