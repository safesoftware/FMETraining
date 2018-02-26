<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Schema Editing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Structural Transformation, Schema Editing</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex1-Complete.fmw</td>
</tr>

</table>


You have just landed a job as technical analyst in the GIS department of your local city.

The team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. You have been assigned to this project and will use FME to provide a dataset of this information.

The first step in this example is to rename existing attributes and create new ones in preparation for the later area calculations.


<br>**1) Start Workbench**
<br>Use the Generate Workspace dialog to create a workspace using these parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Parks\Parks.tab</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training</td>
</tr>

</table>

Yes! Here we write back to the same format of data we are reading from! You may click the Parameters buttons in the Generate Workspace dialog to check the reader/writer parameters, but none of them need changing in this exercise. Note that the writer needs only a folder and not a specific file name.


<br>**2) Rename Feature Type**
<br>FME creates a workspace where the destination schema matches the source. However, the end user of the data has requested parts of the schema are cleaned up.

Inspect the writer feature type parameters. Click in the field labelled Table Name (remember this label is format-specific and in MapInfo we deal with "tables") and change the name from Parks to ParksMaintenanceData:

![](./Images/Img2.200.Ex1.WriterGeneralSchemaEdited.png)


<br>**3) Update Attributes**
<br>Now inspect the user attributes. They will look like this:

![](./Images/Img2.201.Ex1.WriterAttributeSchema.png)

These must be cleaned up so that unnecessary information is removed. Other attributes need to be updated and some extra ones added to store the calculation results. So carry out the following actions:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">RefParkID</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">DogPark</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">Washrooms</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">SpecialFeatures</td>
</tr>

<tr>
<td style="font-weight: bold">Rename Attribute</td>
<td style="">from: NeighborhoodName</td>
<td style="">to: Neighborhood</td>
</tr>

<tr>
<td style="font-weight: bold">Change Type (VisitorCount)</td>
<td style="">from: smallint</td>
<td style="">to: integer</td>
</tr>

<tr>
<td style="font-weight: bold">Add Attribute</td>
<td style="">ParkArea</td>
<td style="">type: Float</td>
</tr>

<tr>
<td style="font-weight: bold">Add Attribute</td>
<td style="">AverageParkArea</td>
<td style="">type: Float</td>
</tr>

</table>

...and click the Parameter Editor "Apply" button. The attribute list should now look like this:

![](./Images/Img2.202.Ex1.WriterAttributeSchemaEdited.png)

Now when the workspace is run the output will be named ParksMaintenanceData.tab and will contain an updated attribute schema.


<br>**4) Un-Expose Source Attributes**
<br>The workspace will now look like this:

![](./Images/Img2.203.Ex1.EditedSchemaOnCanvas.png)

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
Objects on the canvas can be resized (as in the above screenshot) if the feature type name or attribute names are too large to be displayed properly at the default size. The brown markers around the feature types are called <strong>bookmarks</strong>. They too can be resized to better fit their contents.
</span>
</td>
</tr>
</table>

---

Notice there are several source attributes that are not going to be used in the workspace or sent to the output. We can tidy the workspace by hiding these.

Inspect the User Attributes tab on the reader feature type parameters. It will look like this:

![](./Images/Img2.204.Ex1.ReaderAttrSchema.png)

Uncheck the check box for the following attributes, which we do not need:

- RefParkID
- Washrooms
- SpecialFeatures

This is basically the list of attributes we deleted, except for DogParks, which we will make use of in the translation.

Click Apply/OK to confirm the changes.


<br>**5) Save the Workspace**
<br>Save the workspace – it will be completed in further examples. It should now look like this:

![](./Images/Img2.205.Ex1.EditedSchemaOnCanvas.png)


---
<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police Chief Webb-Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Some Writer attributes (ParkArea and AverageParkArea) have red connection arrows because there is nothing yet to map to them, while another (Neighborhood) is just unconnected. 
<br><br>That's OK. I'll let you off with a caution if you promise to connect them later. You can still run this workspace just to see what the output looks like anyway.
</span>
</td>
</tr>
</table>

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
<ul><li>Edit the attributes on a writer schema</li>
<li>Edit the output layer name on a writer schema</li>
<li>Hide attributes on a reader schema</li></ul>
</span>
</td>
</tr>
</table>
