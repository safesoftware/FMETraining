<!--Instructor Notes-->
<!--This exercise uses a basic amount of FME Workbench as a test for students-->
<!--If students have problems now, it is unlikely they will have much success at further exercises-->

<!--Exercise Section-->
<!--NB: In GitBook world we don't give a number to exercises-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Earthquake Processing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Earthquakes (GeoJSON)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to read and process earthquake data and publish it to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Publishing a workspace to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2016\Workspaces\ServerAuthoring\Basics-Ex1-Complete.fmw</td>
</tr>

</table>

---

You're a technical analyst in the GIS department of your local city. You have plenty of experience using FME Desktop, and your department is now investigating FME Server to evaluate its capabilities.

Within minutes of installing FME Server the building starts to shake. You deduce that the two events are not related and in fact a (very minor) earthquake is taking place.

Because of this, and because emergency preparedness is a big topic, you start to wonder if there is anything you can do with FME Server on the subject of earthquakes.



<br>**1) Inspect Feed**
<br>A colleague informs you about a feed of earthquake data at: [http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson](http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson "USGS Earthquake Feed")

Click on that link (or copy/paste it into your web browser) to view the raw data in the feed. It will look something like this:

![](./Images/Img1.6.Ex1.EarthquakeFeed.png)

OK. That looks like something we could handle in FME.

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
If you have lots of experience with FME Workbench - <strong>and if your instructor agrees</strong> - simply open the workspace listed in the header above and skip to step 7
</span>
</td>
</tr>
</table>

---

<br>**2) Start FME Workbench**
<br>Start FME Workbench by selecting it from the Windows start menu. You’ll find it under Start &gt; All Programs &gt; FME Desktop 2016.0 &gt; FME Workbench 2016.0.

Once started, select Readers &gt; Add Reader to start adding a Reader to the workspace. When prompted, enter the following details:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">GeoJSON (Geographic JavaScript Object Notation)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson</td>
</tr>

</table>

Click OK to add the Reader to the workspace.


<br>**3) Inspect Source Data**
<br>Click on the Reader feature type in Workbench and choose the option to Inspect the data:

![](./Images/Img1.7.Ex1.ReaderFeatureTypeInspect.png)

This will open up the source data in the FME Data Inspector and allow you to inspect it:

![](./Images/Img1.8.Ex1.SourceDataInDI.png)
<br><span style="font-style:italic;font-size:x-small">Tiles Courtesy of <a href="http://www.mapquest.com/">MapQuest</a></span>


<br>**4) Add StatisticsCalculator**
<br>Let's calculate some statistics about the earthquakes we are reading. Place a StatisticsCalculator transformer and connect it after the Reader feature type.

Open the parameters dialog. The first thing to do is set Group By to group-by the type attribute:

![](./Images/Img1.9.Ex1.StatsCalcGroupBy.png)

Type represents the type of event measured. Not only are there earthquakes, but also explosions and quarry blasts (browse the data in the Data Inspector if you want to see if there are any).

Next set mag as the attribute to analyze:

![](./Images/Img1.10.Ex1.StatsCalcAttrToAnalyze.png)

This will analyze the magnitude of the events and calculate statistics about them. The final step here is to specify which statistics we want. To do so set:

<table>
<tr><td>Minimum Attribute</td><td>Min Magnitude</td></tr>
<tr><td>Maximum Attribute</td><td>Max Magnitude</td></tr>
<tr><td>Numeric Count Attribute</td><td>Number of Events</td></tr>
<tr><td>Mean Attribute</td><td>Average Magnitude</td></tr>
</table>

Empty all other fields, as we don't need those statistics:

![](./Images/Img1.11.Ex1.StatsCalcAttrToCalculate.png)


<br>**5) Add AttributeRounder**
<br>Let's make sure those statistics are in a readable format. After the StatisticsCalculator place an AttributeRounder transformer. It should be connected to the StatisticsCalculator:Summary output port:

![](./Images/Img1.12.Ex1.AttrRounderConnected.png)

Open the parameters dialog. Set up the transformer to round *Min Magnitude*, *Max Magnitude*, and *Average Magnitude* to 1 decimal place. 


<br>**6) Add Output**
<br>The final task in FME Workbench is to get the calculations out of the workspace. To do so, while we are just testing this exercise, add a Logger transformer after the AttributeRounder.

This will cause the results to be written to the FME log file.


<br>**7) Publish to Server (Step 1)**
<br>Here comes the Server part of the process. In FME Workbench, choose File &gt; Publish to FME Server from the menubar (or select the same tool on the toolbar).

In the first dialog of the wizard you are prompted to enter connection parameters to FME Server.

Enter the parameters provided by your training instructor.

In most cases the parameters will be as follows:

- **FME Server URL:** http://localhost
- **Username:** admin
- **Password:** admin

![](./Images/Img1.44.Ex1.PublishWizard1.png)

You may or may not (probably not) need to enter a port number with the hostname, depending on how the system is set up. 

Click Next to continue. If the credentials are correct a connection will be made and you will move on to the next dialog in the wizard.


<br>**8) Publish to Server (Step 2)**
<br>The next dialog prompts you to choose a repository in which to store the workspace.

For this exercise we’ll create a new repository by clicking the New button. When prompted enter the name Training.

Click OK to close the Create New Repository dialog. Enter a name for the workspace such as Basics-Ex1-Complete.fmw. The Upload Data Files option should be greyed out, because we aren't using any source files in this case.

![](./Images/Img1.45.Ex1.PublishWizard2.png)

Then click Next to continue the wizard.


<br>**9) Publish to Server (Step 3)**
<br>In the final screen of the wizard we can register the workspace for use with various services.

Select the Job Submitter service as this is the only service we are using for now and click Publish to complete publishing the workspace.

![](./Images/Img1.46.Ex1.PublishWizard3.png)

After a workspace is transferred to Server, the log window displays a message reporting which workspace has been published to which repository and for which services.

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
<ul><li>Create a workspace using a GeoJSON feed as the source</li>
<li>Publish a workspace to FME Server using the Publishing Wizard</li>
<li>Create a repository on FME Server using the Publishing Wizard</li>
<li>Register a workspace with the Job Submitter service using the Publishing Wizard</li></ul>
</span>
</td>
</tr>
</table>