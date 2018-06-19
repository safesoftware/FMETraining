<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Neighborhood Averages</span>
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
<td style="border: 1px solid darkorange">Group-By Processing</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Complete.fmw</td>
</tr>

</table>



Let's continue your work on the grounds maintenance project.

The parks team has decided that they do not want the average area of park for the city as a whole. Instead they want the average size of park in each neighborhood; so let's do that for them.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 4. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Begin.fmw


<br>**2) Set Group-By in StatisticsCalculator**
<br>This is a really simple task to do. View the parameters for the StatisticsCalculator transformer and click the 'browse' button next to the Group By parameter. Select the attribute called Neighborhood:

![](./Images/Img2.236.Ex5.StatsCalcGroupBy.png)

Click OK/Apply to apply the changes to the transformer.


<br>**3) Run the Workspace**
<br>Save and then run the workspace.

Inspect the output data in the Table View window of the FME Data Inspector.

You should see that each neighborhood now has its own value for AverageParkArea:

![](./Images/Img2.237.Ex5.StatsCalcGroupByDI.png)

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
<ul><li>Use the group-by parameter in FME transformers</li></ul>
</span>
</td>
</tr>
</table>
