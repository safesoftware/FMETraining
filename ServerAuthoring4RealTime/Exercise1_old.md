<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Shape Dataset Processing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Orthophoto images (GeoTIFF)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Trigger notification for new files</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Notification topics and Directory Watch publications</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

</table>

---

As a technical analyst in the GIS department you want to start trying out notifications. The Directory Watch protocol seems like a good place to start, and you already were thinking about a shared folder where users occasionally put Shape datasets for adding to the corporate database. 


<br>**1) Create Resources Folder**
<br>The first step is to create a Resources folder to copy the data to. Open the FME Server web interface and navigate to Manage &gt; Resources

Browse to the Data folder and create a new sub-folder called ShapeContours:

![](./Images/Img4.58.Ex0.NewDataFolder.png)


<br>**2) Create Topic**
<br>Now to create a publication and topic that will be triggered by a new file. Navigate to Manage &gt; Notifications, click the Publications tab, and then click the New button.

Enter "Incoming Shape Datasets" as the new publication's name. Then click in the text box under Topics to Publish To. Type in ShapeIncomingFile and click on "Click to Add". This will create a new topic and assign it to this publication. 

![](./Images/Img4.57.Ex0.NewPublicationDialog.png)


<br>**3) Create Publication**
<br>Now select Directory Watch as the protocol for this publication. In the dialog that opens below select the newly created resources folder:

![](./Images/Img4.59.Ex0.DirectoryToWatch.png)

Under the Filter setting, remove the Modify and Delete actions. All we really want to monitor are new files arriving, not old ones being removed:

![](./Images/Img4.60.Ex0.DirectoryWatchFilters.png)

Click OK to create the new publication.


<br>**4) Monitor Topic**
<br>Click on the tab for Topic Monitoring. Add the ShapeIncomingFile topic to the list being monitored:

![](./Images/Img4.61.Ex0.DirectoryWatchTopicMonitoring.png)


<br>**5) Test Topic**
<br>Now let's test the topic. Locate the source Shape datasets in C:\FMEData2017\Data\ElevationModel\Contours - select a set of Shape files (.dbf, .prj, .shp, .shx) and create a zip file out of them.

Copy the zip file into the newly created Resources folder. You can do this through the file system (by copying the file to C:\ProgramData\Safe Software\FME Server\resources\data\ShapeContours) or using the web interface. If you use the web interface, open a new window or tab, so as not to stop the topic monitoring.

![](./Images/Img4.62.Ex0.DirectoryWatchDataInFolder.png)

Check back in the topic monitoring window and you will see that the topic has been triggered by the new file:

![](./Images/Img4.63.Ex0.DirectoryWatchTopicMonitoringTriggered.png)

So now we know how the Directory Watch notification works. For now you can put this project to one side - but come back to it later when you've learned how to process this information.
 
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
<ul><li>Create a new Publication</li>
<li>Create a new Topic as part of the Create Publication process</li>
<li>Use Directory Watch to trigger topics/notifications</li>
<li>Test a publication/topic using Topic Monitoring</li></ul>
</span>
</td>
</tr>
</table>   
