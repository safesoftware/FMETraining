<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3.1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data Download System: Workspace Creation</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Orthophoto images (GeoTIFF)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create an FME Server Data Download system for orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating a workspace and running it with Data Download</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2020\Workspaces\ServerAuthoring\SelfServe-Ex1-Complete.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Server Project</td>
<td style="border: 1px solid darkorange">C:\FMEData2020\Projects\ServerAuthoring\SelfServe-Ex1-Complete.fsproject</td>
</tr>

</table>

---

As a technical analyst in the GIS department of your local city you have plenty of experience using FME Desktop, and are just getting started with FME Server.

Other departments frequently ask the GIS team for orthophoto imagery of the city. Their format of choice is usually JPEG. Currently you use FME Desktop to translate the data, adding to your workspace any special requests they have such as a particular resolution, a specific area of interest, or even sets of vector data stamped onto the raster.

However good you are with FME Workbench, it does take time to set up each of these individual requests. It would be far better if the other departments could help themselves to the raster data, with options for all of their special requests built in.

Of course, you very soon realize that a Data Download system implemented on FME Server would be an ideal solution.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">FME Lizard says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
If you have lots of experience with FME Workbench - <strong>and if your instructor agrees</strong> - simply open the workspace listed in the header above and skip to step 6. But make sure you inspect the transformers and their parameters, so you know what you are working with.
</span>
</td>
</tr>
</table>

---

<br>**1) Create Workspace**
<br>Let's start off by creating a basic FME workspace to translate and transform the source raster data. Start FME Workbench and select Readers &gt; Add Reader. When prompted enter these parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">GeoTIFF (Geo-referenced Tagged Image File Format)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2020\Data\Orthophotos\06-07-LM.tif</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Parameters</td>
<td style="">Feature Type Name(s): From File Name(s)</td>
</tr>

<tr>
<td style="font-weight: bold">Workflow Options</td>
<td style="">Single Merged Feature Type</td>
</tr>

</table>

It's important to use the Single Merged Feature Type option because there are many source tiles of data, and we may want to read any of them without having to add them as individual feature types.

The Feature Type Name parameter is important because it will help us later allowing the user to select which layers to read.


<br>**2) Add Writer**
<br>Now we need a Writer. Select Writers &gt; Add Writer from the menubar. When prompted enter these parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">JPEG (Joint Photographic Experts Group)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2020\Output\Training</td>
</tr>

<tr>
<td style="font-weight: bold">Raster File Definition</td>
<td style="">Copy From Reader</td>
</tr>

</table>

Your workspace will now look like this:

![](./Images/Img3.200.Ex1.InitialWorkspace.png)


<br>**3) Add Transformers**
<br>We'll start out with two transformers in our workspace; a RasterResampler and a RasterMosaicker. So place one of each of these and connect up everything in the workspace:

![](./Images/Img3.201.Ex1.WorkspaceWithTransformers.png)


<br>**4) Set Transformer Parameters**
<br>Inspect the RasterResampler's parameters and set:

<table>
<tr><td style="font-weight: bold">Resolution Specification</td><td>Cell Spacing</td></tr>
<tr><td style="font-weight: bold">X Cell Spacing</td><td>5</td></tr>
<tr><td style="font-weight: bold">Y Cell Spacing</td><td>5</td></tr>
</table>

![](./Images/Img3.202.Ex1.RasterResamplerParams.png)

You may inspect the RasterMosaicker's parameters, but there aren't any that need changing at the moment.


<br>**5) Save and Run Workspace**
<br>Save the workspace and - just to ensure that all is well - run it in FME Workbench. The result should be a JPEG file (06_07_LM.jpg) along with a world file (06_07_LM.wld).

![](./Images/Img3.203.Ex1.TestOutput.png)


<br>**6) Publish Workspace**
<br>Now publish the workspace to FME Server. Register it with the Data Download service. Remember. you'll need to either publish the data with the workspace or upload it to an FME Server Resources folder.


<br>**7) Run Workspace**
<br>Log in to the FME Server web interface, locate the workspace, and run it.

The workspace will run and you will be presented with a hyperlink to a zip file of the output dataset:

![](./Images/Img3.204.Ex1.DataDownloadResult.png)

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
<ul><li>Create a workspace to read and write raster data</li>
<li>Publish and run a workspace using the Data Download service</li></ul>
</span>
</td>
</tr>
</table>
