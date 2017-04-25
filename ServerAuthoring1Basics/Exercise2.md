<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Daily Database Updates</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Firehalls (GML)<br>Neighborhoods (KML)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to read and process departmental data and publish it to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Examining the FME Server interface and running a workspace</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

</table>

---

For the exercises in this chapter, you are a technical analyst in the GIS department of your local city. You have plenty of experience using FME Desktop, and your department is now investigating FME Server to evaluate its capabilities.

There are many departments within the city, and one of your tasks is to take the data from each department and merge it together into a single, corporate database.

Because each department produces their datasets in a different format and style, you use FME for this task, and carry it out on a weekly basis.   

After creating a workspace to carry out this translation, and publishing it to FME Server, you now wish to log in to Server to run that workspace. 


<br>**1) Connect to Server**
<br>To log in to the server interface either select the Web User Interface option from the start menu or - in your web browser - enter the address to your FME Server.

---

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
When FME Server is installed on either physical or virtual hardware, the address is http://&lt;servername&gt;/fmeserver
<br><br>If you are using FME Cloud, then the address is: http://&lt;server name&gt;.fmecloud.com/fmeserver
</span>
</td>
</tr>
</table>

---

This will open the web user interface login screen for the FME Server being used. Bookmark this web address, since you will use this link quite often.


<br>**2) Log In to Server**
<br>In the User Login dialog, enter a username and password for your FME Server account. A common username/password combination for a training installation is admin/admin

![](./Images/Img1.217.Ex2.LogInWindow.png)

Click the Login button.


<br>**3) Examine the User Interface**
<br>This is your primary method for interacting with FME Server.

Notice that one of the windows is labelled as Last Published Workspaces. Here you should be able to find the workspace published in Exercise 1:

![](./Images/Img1.218.Ex2.StarWorkspace.png)

Clicking the star icon will set this workspace as a favourite, making it available under the list of favourites panel:

![](./Images/Img1.219.Ex2.StarredWorkspace.png)

We'll run the workspace shortly, but perhaps first we should make sure FME Server is running correctly (the fact that we could log in is a good sign) and that we are licensed and have engines running.


<br>**4) Examine the User Interface**
<br>Click Engines & Licensing on the ADMIN part of the interface menu. This will open up the licensing section. You should see a message informing you that FME Server is licensed and a list of the engines available:

![](./Images/Img1.220.Ex2.LicensingInfo.png)

---

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
If your machine is unlicensed, or is missing engines, then check with your instructor for troubleshooting tips
</span>
</td>
</tr>
</table>

---

<br>**5) Run Workspace**
<br>Click the FME Server button in the very top-left of the interface. This will return you to the Server interface home page.

Click on the published workspace in the Favourite Workspace panel to open the web page for this workspace.

The workspace page shows a few options, the first of which are for the repository, workspace, and service. These should already be filled in with values:

![](./Images/Img1.221.Ex2.RunWorkspaceDialog.png)

Because this workspace has a few published parameters, they are also listed; but we can ignore these for now (we'll deal with source datasets and the like shortly). 

So, simply click the Run button to run the workspace. The workspace will run to completion and a message to that effect will appear:

![](./Images/Img1.222.Ex2.RanWorkspace.png)


<br>**6) Examine Jobs Page**
<br>Click Jobs on the main menu. A list of previously run jobs will open, including the one we just ran:

![](./Images/Img1.223.Ex2.JobsWindow.png)

Notice some interesting points of the interface:

1. There are links to show Completed jobs (the default), Queued Jobs, and Running Jobs.
2. There is a drop-down list that allows you to filter whose jobs are being shown.
3. Jobs that are successful and which fail are differentiated using a different icon.
4. The jobs are displayed in the chronological order in which they were started.

Click on your job to inspect the results in more detail. You will be able to see details about the job including the time at which it was submitted, queued, started, finished, and delivered; the exact request made to FME Server; and the full results of the translation. You may also click the View Log button to inspect the FME translation log file.

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
Remember, this workspace did not write any data, only sent it to a Null writer. So, for now, to view any results search for the summary in the log file.
</span>
</td>
</tr>
</table>

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
If you want to see a job in a different state then we'll have to slow this workspace down some.
<br><br>Open the workspace in FME Workbench and add a Decelerator transformer (say, before the Reprojector). Set it to delay the workspace by five (5) seconds per feature. Publish the workspace back to FME Server and re-run it.
<br><br>Now the workspace will take 30+ seconds to run and you should be able to find it under the Running state. Also, if you run it three or four times in quick succession, then you will have more jobs than engines and be able to find some jobs in the Queued state.   
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
<ul><li>Log in to FME Server and check that it is running and licensed</li>
<li>Locate a workspace using the Last Published list</li>
<li>Run a workspace and inspect the job history to confirm it ran correctly</li>
<li>Find and upload resources to FME Server</li>
<li>Check the parameters for cleanup tools</li></ul>
</span>
</td>
</tr>
</table>
