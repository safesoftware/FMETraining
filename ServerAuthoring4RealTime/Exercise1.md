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
<td style="border: 1px solid darkorange">Contour vector features (Esri Shapefile)</td>
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

As a technical analyst in the GIS department you want to start experimentiing with notifications in FME Server. The Directory Watch protocol seems like a good place to start, and you already were thinking about a shared folder where users occasionally put Shape datasets for adding to the corporate database. 


<br>**1) Create Resources Folder**
<br>The first step is to create a Resources folder to copy the data to. Open the FME Server web interface and navigate to Manage &gt; Resources

Browse to the Data folder and create a new sub-folder called ShapeContours:

![](./Images/Img4.400.Ex1.NewDataFolder.png)

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
This exercise utilizes the FME Server Resource folders, but there is also native support in FME Server to watch for new resources in Amazon S3 Buckets, Dropbox, and FTP.
<br>Using the same concepts described here, you could use one of these protocols instead of Directory Watch.
</td>
</tr>
</table>


<br>**2) Create Topic**
<br>Now to create a publication and topic that will be triggered by a new file. Navigate to Manage &gt; Notifications, click the Publications tab, and then click the New button.

Enter "Incoming Shape Datasets" as the new publication's name. Then click in the text box under Topics to Publish To. Type in ShapeIncomingFile and click on "Click to Add". This will create a new topic and assign it to this publication. 

![](./Images/Img4.401.Ex1.NewPublicationDialog.png)


<br>**3) Create Publication**
<br>Now select Directory Watch as the protocol for this publication. In the dialog that opens below select the newly created resources folder:

![](./Images/Img4.402.Ex1.DirectoryToWatch.png)

Under the Filter setting, remove the Modify and Delete actions. All we really want to monitor are new files arriving, not old ones being removed:

![](./Images/Img4.403.Ex1.DirectoryWatchFilters.png)

Change the Poll Interval to 1 Minute and click OK to create the new publication.


<br>**4) Monitor Topic**
<br>Click on the tab for Topics. Select the ShapeIncomingFile topic and click Monitor. This will start Topic Monitoring:

![](./Images/Img4.403.Ex1.DirectoryWatchTopicMonitoring.png)


<br>**5) Test Topic**
<br>Now let's test the topic. Locate the source Shape datasets in C:\FMEData2017\Data\ElevationModel\Contours - select a set of Shape files (.dbf, .prj, .shp, .shx) and create a zip file out of them.

Copy the zip file into the newly created Resources folder. You can do this through the file system (by copying the file to C:\ProgramData\Safe Software\FME Server\resources\data\ShapeContours) or using the FME Server Web UI. If you use the web interface, open a new window or tab, so we can continue to monitor the ShapeIncomingFile topic.

![](./Images/Img4.404.Ex1.DirectoryWatchDataInFolder.png)

Check back in the Topic Monitoring window and you will see that the topic has been triggered by the new file:

![](./Images/Img4.405.Ex1.DirectoryWatchTopicMonitoringTriggered.png)

Now we know how the Directory Watch notification works! We will see in subsequent exercises how to process this information.
 
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
