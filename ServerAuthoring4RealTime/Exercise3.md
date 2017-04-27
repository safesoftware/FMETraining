<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Building Updates Notification System</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Building footprints (Esri Shapefile)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Triggering real-time updates to databases</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Processing Directory Watch notifications</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2017\Workspaces\ServerAuthoring\RealTime-Ex3-Complete.fmw</td>
</tr>

</table>

---

Now that you have learned how to run a workspace in response to a notification, it's time to take that basic workspace and adjust it for your overall goal: to provide real-time updates to your corporate database.

The next step towards achieving this is understanding how to extract information from the notifications and configure an FME Workspace to process that incoming data.

---

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
This exercise continues where Exercise 2 left off. You must have completed Exercise 2 to carry out this exercise.
</td>
</tr>
</table>

---

<br>**1) Create Workspace**
<br>Start FME Workbench and begin with an empty workspace. 

Select Readers &gt; Add Reader from the menubar. When prompted set the parameters as follows: 

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Text File</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2017\readme.txt</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Parameters</td>
<td style="">Read Whole File at Once: Yes</td>
</tr>

</table>

It doesn't matter what text file we use as the source right now; setting the source dataset in this step is only to satisfy the Text Reader requirements. At run time, the source dataset will be replaced by the content of the incoming message.


<br>**2) Add JSONFlattener**
<br>Now add a JSONFlattener transformer to the workspace, after the Text File Reader. The incoming message is formatted as JSON, and this transformer will expose attributes on the canvas - making them available to work with.

Open the parameters dialog and select *text&#95;line&#95;data* as the source of the JSON content.

Add Logger transformers after the JSONFlattener.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Instead of using Text Reader &gt; JSONFlattener we could have used the JSON Reader. Why didn't we? The JSON Reader requires a source file with valid schema. At this stage in the exercise, we do not have a file with this structure yet.
</td>
</tr>
</table>

---

<br>**3) Publish to FME Server**
<br>Publish the workspace to FME Server, registering it under the Job Submitter service. 


<br>**4) Update Subscription**
<br>Now log in to the FME Server web interface and navigate to the Notifications page. 

Click on the Subscriptions tab and select the existing "Process Building Updates" Subscription to edit it.

Change the specified workspace to the one uploaded in the previous step. Next to the Source Text File field, select the checkbox for *Get Value from Topic Message*.

![](./Images/Img4.410.Ex3.ValueFromTopicMessage.png)

Click OK to update the Subscription.


<br>**5) Test Topic**
<br>Locate the source Shape datasets in C:\FMEData2017\Data\Engineering\BuildingFootprints - select a set of Shapefiles (.dbf, .prj, .shp, .shx) and create a zip file out of them (as you did in Exercise 2).

Copy the zip file into the newly created Resources folder. You can do this through the file system (by copying the file to C:\ProgramData\Safe Software\FME Server\resources\data\BuildingUpdates) or using the FME Server web interface. 


<br>**6) Check Results**
<br>Open the Jobs page in the web interface. Under completed jobs should list the workspace you updated in the subscription. View or download the log file and look for the logged feature. You should find it has an attribute containing JSON, and a number of attributes extracted from the JSON. 

<table>
<tr><td>dirwatch_publisher_action</td><td>CREATE</td></tr>
<tr><td>dirwatch_publisher_content</td><td>ENTRY_CREATE C:\ProgramData\Safe Software\FME Server\resources\data\BuildingUpdates\update002.zip</td></tr>
<tr><td>dirwatch_publisher_path</td><td>C:\ProgramData\Safe Software\FME Server\resources\data\BuildingUpdates\update002.zip</td></tr>
</table>

So now we know what the data looks like and can process it accordingly. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. Flibble says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
You may recognize these attributes from the Topic Monitoring exercise - indeed you can view the same information there without going through this process of adding Logger transformers!
</span>
</td>
</tr>
</table>

---


<br>**7) Edit JSONFlattener Transformer**
<br>Back in FME Workbench open the JSONFlattener transformer parameters. Under Attribute to Expose add the attribute *dirwatch&#95;publisher&#95;path*


<br>**8) Add FeatureReader Transformer**
<br>Now remove the Logger transformers and add a FeatureReader transformer to the output of the JSONFlattener:

![](./Images/Img4.411.Ex3.FeatureReaderInWorkspace.png)

This is a transformer that will let us read the contents of the dataset into the workflow mid-translation. Open the parameters dialog and set the following values:

<table>
<tr><td><strong>Reader Format</strong></td><td>Esri Shapefile</td></tr>
<tr><td><strong>Reader Dataset</strong></td><td>Select Attribute Value &gt; dirwatch&#95;publisher&#95;path</td></tr>
<tr><td><strong>Output Port</strong></td><td>Single Output Port</td></tr>
</table>

Select to have a Single Output Port:

![](./Images/Img4.412.Ex3.FeatureReaderParameters.png)

Click OK to close the dialog. You may receive a warning message, but it can be safely ignored.


<br>**9) Add Writer**
<br>Having read the data from a Shapefile, we can now add it to the corporate database.

Select Writers &gt; Add Writer from the menubar. When prompted set the parameters as follows: 

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">SpatiaLite</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2017\Data\Engineering\BuildingFootprints\building_footprints.sl3</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Parameters</td>
<td style="">Overwrite Existing Database: No<br>Drop Existing Tables: No</td>
</tr>

<tr>
<td style="font-weight: bold">Add Feature Types</td>
<td style="">Table Definition: Manual</td>
</tr>

</table>

In the new feature type that is created, simply change the name to *building_footprints*:

![](./Images/Img4.413.Ex3.FeatureTypeName.png)

Click OK to close the dialog and connect the new feature type to the FeatureReader transformer's &lt;Generic&gt; output port.

![](./Images/Img4.414.Ex3.FinalWorkspace.png)


<br>**10) Republish Workspace**
<br>Publish the workspace back to FME Server. If you have the same FME Workbench session open from the start of this exercise, you can use the Republish option on the toolbar or under the File menu.

![](./Images/Img4.428.Ex3.RepublishWorkspace.png)


<br>**11) Edit Subscription**
<br>Navigate to the Notifications page and open the Process Building Updates Subscription for editing. The settings should now include one for the output database. Specify to write the database into the Resources > Output folder:

![](./Images/Img4.415.Ex3.OutputDatabaseSelection.png)


<br>**12) Test Solution**
<br>Now test the solution by putting more zipped Shapefile data into the Directory Watch folder. You will find that each dataset put into the folder is added to the SpatiaLite database:

![](./Images/Img4.416.Ex3.ViewOutputInDataInspector.png)

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
<ul><li>Identify JSON attributes on an incoming Topic Message</li>
<li>Use a FeatureReader transformer to read the dataset added to watched folder</li></ul>
</span>
</td>
</tr>
</table>   
