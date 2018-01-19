<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Calculating Statistics</span>
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
<td style="border: 1px solid darkorange">Content Transformation. Schema Mapping</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Complete-Advanced.fmw</td>
</tr>

</table>


Let's continue your work on the grounds maintenance project.

In case you forgot, the team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. 

In this part of the project we’ll calculate the size and average size of each park, and ensure that information is correctly mapped to the destination schema.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 2. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Begin.fmw


<br>**2) Add an AreaCalculator Transformer**
<br>To measure the area of each park feature, an AreaCalculator transformer must be used. “Calculator” is the term for when FME computes new attribute values.

Click onto the connection between Tester:Passed port and the writer feature type *ParksMaintenanceData*. Start typing the letters “areac”. You will see the Quick Add list of matching transformers appear beneath.

Select the transformer named AreaCalculator by double-clicking it:

![](./Images/Img2.217.Ex3.QuickAddAreaCalculator.png)


<br>**3) Add a StatisticsCalculator Transformer**
<br>Using the same method, place a StatisticsCalculator transformer between the AreaCalculator:Output port and the *ParksMaintenanceData* feature type.

**BUT!** Do not click anything else yet! The transformer will now look like this:

![](./Images/Img2.218.Ex3.StatsCalcDefaultConnections.png)

By default the Summary port has been connected, and we need the Complete port connected instead. But notice the little pop-up icons over the top. Click the right-hand icon (the one with the ? character). This pops up a further list of ports:

![](./Images/Img2.219.Ex3.StatsCalcPopUpButtons.png)

Click on the Summary port entry to disconnect that, and then on the Complete port entry to connect that:

![](./Images/Img2.220.Ex3.StatsCalcPopUpButtonsEdited.png)

Notice how the connection has been changed from the incorrect Summary port to the correct Complete port.

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
These pop-up menus are a great help in schema mapping and other feature connections.
</span>
</td>
</tr>
</table>

---

The latter part of the workspace now looks like this:

![](./Images/Img2.221.Ex3.StatsCalcInCanvas.png)


<br>**4) Check AreaCalculator Settings**
<br>Inspect the AreaCalculator parameters:

![](./Images/Img2.222.Ex3.AreaCalcParameters.png)

The default settings cause the calculated value to be placed into an attribute called _area. However, the *ParksMaintenanceData* schema requires an attribute called ParkArea, so change this parameter to create the correct attribute:

![](./Images/Img2.223.Ex3.AreaCalcEditedParameters.png)

Once you click OK or Apply notice that the attribute on the writer feature type is now flagged as connected.


<br>**5) Check StatisticsCalculator Settings**
<br>A red icon indicates the StatisticsCalculator has parameters that need to be defined.

Inspect the StatisticsCalculator transformer's parameters. The attribute to analyze is the one containing the calculated area; so select ParkArea:

![](./Images/Img2.224.Ex3.StatsCalcParameters1.png)

Examine what the default setting is for an attribute name for average (mean) park size. Currently it doesn't match the *ParksMaintenanceData* schema, which requires an attribute named AverageParkArea.

Change the attribute from _mean to AverageParkArea. For Best Practice reasons, delete/unset any StatisticsCalculator output attributes that aren't required (for example _range and _stdev).

![](./Images/Img2.225.Ex3.StatsCalcParameters2.png)


<br>**6) Run the Workspace**
<br>Add another bookmark if you wish, run the workspace, and inspect the result of the translation using the FME Data Inspector:

![](./Images/Img2.226.Ex3.DITableView.png)

The Table View window shows the area of each park and the average area of all parks.


<br>**7) Save the Workspace**
<br>Save the workspace – it will be completed in further examples.


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
Notice that the numbers in the Table View show the results have been calculated to 12 decimal places. This is in excess of the precision that you require. As an advanced task - if you have time - use the AttributeRounder transformer to reduce the values to just 2 decimal places.
<br><br>If you wish, you can also calculate the smallest, largest, and total park areas; but don't forget to add them to the writer schema if you want them to appear in the output.
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
<ul><li>Carry out content transformation with transformers (AreaCalculator, StatisticsCalculator)</li>
<li>Manage transformer connections using pop-up buttons</li>
<li>Use transformer parameters to create attributes that match the writer schema</li></ul> 
</span>
</td>
</tr>
</table>
