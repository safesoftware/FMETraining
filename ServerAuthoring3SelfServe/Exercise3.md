<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3.3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data Download System: Published Parameters</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Community Mapping (Esri File Geodatabase)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create an FME Server Data Download system community mapping data, allowing the user to choose the format, layers, and area of interest</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating published parameters for user control in Data Download</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2020\Workspaces\ServerAuthoring\SelfServe-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2020\Workspaces\ServerAuthoring\SelfServe-Ex3-Complete.fmw</td>
</tr>

</table>

---

As a technical analyst in the GIS department of a city, you have just commenced an initiative to allow other departments to download community mapping data, rather than having to ask you to create it for them. Not only will their requests be processed quicker, but you will also spend less time on that task.

So far you have created a workspace that allows users to choose the format and layers of the data they wish to download.

Now you need to add a Geometry published parameter to let users interactively choose their area of interest.

<br>**1) Open Workspace**
<br>Open C:\FMEData2020\Workspaces\ServerAuthoring\SelfServe-Ex3-Begin.fmw.

<br>**2) Inspect Published Parameters**
<br>The starting workspace is in-progress. It already has published parameters that let users choose the output format and coordinate system. You can find them by looking at Navigator > Published Parameters. Right-click COORD_SYS and choose Edit Definition to view its configuration.

IMAGE

You can see it is of type Coordinate System Name and will let the user pick any output coordinate system. Click Cancel.

Right-click FORMAT and choose Edit Definition to view its configuration:

IMAGE

You can see this parameter lets the user choose the output format for the data they receive. The default is Microsoft Excel. You can click the ellipsis button next to Configuration to view the options for this Choice with Alias parameter.

IMAGE

This gives the user the option of four output formats (GeoJSON, OGC GeoPackage, Esri Shapefile, or Microsoft Excel). Using Choice with Alias like this lets you provide a set of formats or coordinate systems to the user, instead of letting them pick from the entire list. This option can be beneficial as it is less overwhelming to the user and can prevent incorrect outcomes. Click Cancel twice to close the parameter dialog.

<br>**3) Create a Geometry Published Parameter**
<br>First you need to add a Geometry published parameter. In the Navigator, right-click User Parameters > Create User Parameter:

IMAGE

In the Add/Edit User Parameter window enter the following:

<table>
<tr><td>Type</td><td>Geometry</td></tr>
<tr><td>Name</td><td>GEOM_COORDS</td></tr>
<tr><td>Prompt</td><td>Select construction area:</td></tr>
<tr><td>Published</td><td>Checked</td></tr>
<tr><td>Optional</td><td>Unchecked</td></tr>
<tr><td>Attribute Assignment</td><td>Off</td></tr>
</table>

For Configuration, click on the ellipsis and enter the following:

<table>
<tr><td>Geometry Types</td><td>Box, Polygon, Line<td></tr>
<tr><td>Specify initial bounds for map display</td><td>Checked<td></tr>
<tr><td>Top (-90..90)</td><td>49.2548<td></tr>
<tr><td>Left (-180..180)</td><td>-123.244<td></tr>
<tr><td>Bottom (-90..90)</td><td>49.3034<td></tr>
<tr><td>Right (-180..180)</td><td>-123.071<td></tr>
</table>

The initial bounds will be the area that the map displays in FME Server. Larger bounds will have the map zoomed out, and smaller bounds will have the map zoomed in.

IMAGE from KB

Click OK to close the parameter dialog.

<br>**4) Create the Area of Interest Polygon**
<br>Now that we have set up the geometry published parameter, we need to use it within the workflow. Add a GeometryReplacer after the Creator transformer to the canvas.

IMAGE from KB

Open the parameters for the GeometryReplacer. Set the Geometry Encoding to GeoJSON and then set the Geometry Source to the GEOM_COORDS published parameter.

IMAGE from KB

<br>**5) Reproject the Area of Interest**
<br>We will want to ensure that FME knows our data is in LL84 as this is what the geometry published parameter accepts as values. Add a CoordinateSystemSetter transformer after the GeometryReplacer. In the parameters, set the Coordinate System to LL84.

IMAGE from KB

Our source data is in UTM83-10. It is more appropriate to buffer and intersect data in a projected coordinate system, so we will reproject both streams of data to UTM83-10. Add the first Reprojector after the CoordinateSystemSetter. Set the Destination Coordinate System to UTM83-10.

IMAGE from KB

Your workflow should look like this once both the coordinates are set:

IMAGE from KB

<br>**6) Buffer the Area of Interest**
<br>We need to add a 100-meter buffer around the area of interest to find which neighboring residents might be affected by construction noise and must be notified. Add a Bufferer transformer connected to the first Reprojector. In the parameters, set the Buffer Distance to 100 and set the Buffer Distance Units to Meters.

IMAGE from KB

<br>**7) Clip the Addresses to the Area of Interest**
<br>Now we need to apply the buffered area of interest to our data. To do this we will use a Clipper transformer. Add a Clipper transformer to the canvas and connect the Bufferer to the Clipper input port. Then connect the Reprojector_2 to the Clippee input port. In the Clipper parameters, enable Merge Attributes.

IMAGE from KB

<br>**8) Clean up Attributes**
<br>One final step before we can write out our data is to clean up the attributes. Add an AttributeKeeper to the canvas and connect it to the Inside output port on the Clipper_2.

In the parameters, for Attributes to Keep, select:
- OWNERNM1
- PSTLADDRESS
- PSTLCITY
- PSTLPROV
- POSTALCODE

<br>**9) Test Writing Results to Shapefile**
<br>Let's test our workspace by writing the results to a Shapefile. Make sure your AttributeKeeper is connected to the NotifyList writer feature type and run your workspace. Select LL84 as the coordinate system and Esri Shapefile as the output format.

For the Geometry parameter, we have to supply GeoJSON to test on FME Desktop. On FME Server you can use a web map. Paste the following GeoJSON code in to test:

```javascript
<code>{"type":"Polygon","coordinates":[[[-123.131762,49.282752],[-123.132148,49.282465],[-123.131579,49.282087],[-123.131139,49.282332],[-123.131762,49.282752]]]}
```

When the translation finishes, click the NotifyList writer feature type once to select it, and then click View Written Data. The address to notify, those within 100m of the area of interest, should appear in the Visual Preview window.

IMAGE

---

<!--Tip Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
We have provided the test GeoJSON code for you here. If you want to get your own GeoJSON to test, you can do the following. You can publish your unfinished workspace to FME Server, fill out the Geometry parameter, and copy the resulting GeoJSON code. Alternatively, you can use an online service to generate the GeoJSON for you, e.g. <a href="https://geojson.io/">https://geojson.io/</a>. Just remember the parameter expects a single feature, not a </span><span style="font-size:larger"><code>FeatureCollection</code>
</span>
</td>
</tr>
</table>

---

<br>**10) Publish to FME Server**
<br>

<br>**11) Test on FME Server**
<br>

Then you need to use the parameter in the workspace. A common workflow is to use a GeometryBuilder to create the area of interest using the published parameter.

IMAGE

Then you need to make sure it's in the right coordinate system using a Reprojector.

IMAGE

After that, you can use a FeatureReader to read the data using the same method described above (the user-defined boundary is the Initiator). After that you can use a Clipper to clip the data to the user-defined boundary. This step is necessary because sometimes the data that is read in by the FeatureReader might still go outside the boundaries defined by the user. For example, a long road feature might be partly within their boundaries, but the entire feature is read in by the FeatureReader. The Clipper will transform the feature so it is exactly within the user's boundary.

After publishing to FME Server, the user will see a web map where they can interactively select their area of interest.

---

<!--Exercise Congratulations Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Create an integer user parameter and apply it to two transformer parameters</li>
<li>Create a choice user parameter and apply it to a writer feature type parameter</li>
<li>Publish a workspace and use published parameters</li></ul>
</span>
</td>
</tr>
</table>
