<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Structural Transformation</span>
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
<td style="border: 1px solid darkorange">Structural Transformation with Transformers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Complete-Advanced.fmw</td>
</tr>

</table>


Let's continue your work on the grounds maintenance project.

In case you forgot, the team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. 

In this part of the project we’ll filter out dog parks from the source data (as these have a different scale of maintenance costs) and write them to the log window. We'll also handle the renamed attribute NeighborhoodName.


<br>**1) Start FME Workbench**
<br>Start FME Workbench and open the workspace from the previous exercise. Alternatively you can open
C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Begin.fmw.


<br>**2) Add Transformer**
<br>Let's first handle the source attribute NeighborhoodName, which was renamed Neighborhood on the writer but not yet connected. 

We could do this by simply drawing a connection, but it's generally better to use a transformer. There are two transformers we could use. One is called the AttributeRenamer and the other - which we shall use here - is the AttributeManager.

Therefore click on the feature connection from reader to writer feature type:

![](./Images/Img2.206.Ex2.SelectedFeatureConnection.png)

Start to type the phrase "AttributeManager". This is how we can place a transformer in the workspace. As you type, FME searches for a matching transformer. When the list is short enough for you to see the AttributeManager, select it from the dialog (double-click on it):

![](./Images/Img2.207.Ex2.QuickAddAttrManager.png)

This will place an AttributeManager transformer like so:

![](./Images/Img2.208.Ex2.AttrManagerOnCanvas.png)

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
For a great tip on adding transformers see #5 in our list of <strong><a href="http://blog.safe.com/2014/10/fmeevangelist128/">The Top Ten FME Tips of All Time!</a></strong>
</span>
</td>
</tr>
</table>

---

<br>**3) Set Parameters**
<br>View the AttributeManager parameters (either its dialog or in the Parameter Editor window). It will look like this:

![](./Images/Img2.209.Ex2.AttrManagerParameters.png)

Notice that all of the attributes on the stream in which it is connected will automatically appear in the dialog. 

Where the Input Attribute field is set to NeighborhoodName, click in the Output Attribute field. Click on the button for the drop-down list and in there choose Neighborhood as the new attribute name to use:

![](./Images/Img2.210.Ex2.AttrManagerEditingAttr.png)

In response the Action field will change to read *Rename*.

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
Neighborhood only appears in the list because it already exists on the writer schema. If we had done this step before editing the writer schema, we would have had to manually enter the new attribute name in this dialog.
</span>
</td>
</tr>
</table>

---

Click OK to close the dialog. Now in the Workbench canvas window you will see the Neighborhood attribute is flagged with a green arrow, to confirm that a value is being provided to that attribute.

![](./Images/Img2.211.Ex2.AttrManagerAfterEditing.png)


<br>**4) Add Transformer**
<br>Now we should remove dog parks from the data, because these have their own set of costs.

This can be done with a Tester transformer. Click on the connection from the AttributeManager output port to the ParksMaintenanceData feature type on the Writer.

Start typing the word Tester. When you spot the Tester transformer double-click on it to add one to the workspace. After tidying up the layout of the canvas, the workspace will now look like this:

![](./Images/Img2.212.Ex2.TesterOnCanvas.png)

Notice that the Passed output port is the one connected by default.


<br>**5) Set Parameters**
<br>Inspect the parameters for the Tester transformer. Click in the Left Value field and from there click the down arrow and choose Attribute Value > DogPark:

![](./Images/Img2.213.Ex2.TesterAttrSelection.png)

For the Right Value click into the field and type the value N. The operator field should be filled in automatically as the equals sign (=), which is what we want in this case.

![](./Images/Img2.214.Ex2.TesterTestClause.png)

Click OK to accept the values and close the dialog.

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
The test is for DogParks=N because we want to keep those features, and it is the Passed port that is connected. If the test was DogParks=Y then the Failed port would be the one to connect.
</span>
</td>
</tr>
</table>

---

<br>**6) Add Transformer**
<br>We are now filtering out dog parks from our data, using a test on an attribute value. The question is, what should we do with the features we have filtered out? There are many things we could do, but for now we'll simply log the information to the FME log window.

To do this, right-click on the Tester Failed port and choose the option Connect Logger:

![](./Images/Img2.215.Ex2.TesterConnectLogger.png)

A Logger transformer will be added to the workspace. This will record all incoming features to the log window:

![](./Images/Img2.216.Ex2.WorkspaceWithLogger.png)

Loggers inserted by this method are named after – and reported in the log with – the output port they are connected to, here Tester_Failed.


<br>**7) Run Workspace**
<br>Save and run the workspace. It is not yet complete but running it will prove that everything is working correctly up to this point.


---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Readers and writers on the canvas had a bookmark object added around them automatically. You can do the same to the transformers by selecting them all and either clicking Bookmark on the toolbar or pressing the Ctrl+B keys. Give the bookmark a name of your choice that describes the actions being carried out. 
<br><br>A bookmark is an example of what we call <strong>Best Practice</strong> in FME.
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
<ul><li>Add transformers to a workspace</li>
<li>Carry out schema mapping with the AttributeManager transformer</li>
<li>Filter data using the Tester transformer</li>
<li>Record data using the Logger transformer</li>
<li>Add bookmarks to a workspace</li></ul>
</span>
</td>
</tr>
</table>