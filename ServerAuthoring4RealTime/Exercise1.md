<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4.1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Building Updates Automation</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Building footprints (Esri Shapefile)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Trigger notification for new files</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Directory Watch Trigger</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Server Project</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Server Project</td>
<td style="border: 1px solid darkorange">C:\FMEData2020\Projects\ServerAuthoring\RealTime-Ex1-Complete.fsproject</td>
</tr>

</table>

---

As a technical analyst in the GIS department, you want to start experimenting with Automations in FME Server. The Directory Watch protocol seems like a good place to start, and you were already thinking about a shared folder where users place Shapefile datasets for adding to, or updating, the corporate database.


<br>**1) Create Resources Folder**
<br>The first step is to create a Resources folder to upload the data. Open the FME Server web interface and navigate to the Resources page.

Browse to the Data folder and create a new subfolder called BuildingUpdates:

![](./Images/Img4.400.Ex1.NewDataFolder.png)

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
This exercise utilizes the FME Server Resource folders, but you could also watch a Directory outside of FME Server Resources by creating a Resource Connection or reference a shared UNC path.
<br>There is also native support in FME Server to watch for new resources in Amazon S3 Buckets, Dropbox, and FTP. Using the same concepts described here, you could use one of these protocols instead of Directory Watch.
</td>
</tr>
</table>

---

<br>**2) Create Automation**
<br>Now to create the Automation that will watch the BuildingUpdates Directory for incoming files. Navigate to Automations > Build on the side menu bar. In the Getting Started dialog that appears when you go to the Automations page for the first time, click on the Build tab and click Create New to start a new Automation.

By default, Automations starts in guided mode. This means that there is already a Trigger node on the canvas but it will still need to be configured.

Start by selecting the Trigger and a parameter box will appear on the right hand side of the canvas.
Select Directory modified from the drop-down list as the Trigger for this Automation.

![](./Images/Img4.401.Ex1.NewTriggerDialog.png)

<br>**3) Define Trigger Parameters**
<br>After selecting a Trigger type a list of configurable parameters appears in the dialog. Click the ellipsis button to browse the FME Server Resources and set the Directory to Watch parameter. Select the newly created BuildingUpdates folder under the Data subfolder:

![](./Images/Img4.402.Ex1.DirectoryToWatch1.png)

Leave the Watch Subdirectories and Receive Notifications for Folders parameters set to No, since we are only interested in monitoring for files in the BuildingUpdates folder directly.

Then for the Filter parameter remove the MODIFY and DELETE actions. Since we are looking to add to the corporate database, in this example we are only interested in monitoring for new files arriving, not old ones being changed or removed:

![](./Images/Img4.403.Ex1.DirectoryWatchFilter.png)

Lastly change the Poll Interval to 30 Seconds and then in the bottom left corner, click on the Validate button to ensure the trigger was set up correctly. Now click Apply to save these parameters. In the canvas the Trigger node will update to show it is a Directory Watch.

![](./Images/Img4.404.Ex1.CompleteDirectoryWatch.png)


Save the Automation by selecting Menu > Save as and name the Automation "Incoming Building Footprints".

<br>**4) Log Message**
<br>Before we start the Automation we need to add an Action so the Trigger protocol can parse the notifications onwards. Before processing the data we first want to check the Directory Watch trigger is working as expected. To do this we can send the incoming messages to a log file located on FME Server.

Select the Next Action node and set the Action to Log.

Click on the drop-down arrow for the Message parameter and select General > Event as JSON because in this instance we want to record the entire incoming message from the Directory Watch protocol.

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
A trigger stores the incoming message event details as JSON however for the standard protocols FME is able to flatten the JSON down into its separate elements so the workspace or other subsequent action does not need to be able to handle this.
<br>If your trigger contains information from a webhook that is buried in the JSON you can parse the entire message into a parameter to flatten using JSON transformers in FME Workbench.
</span>
</td>
</tr>
</table>

---
Since this is for testing we can save the log file to a temporary location that is frequently cleaned up by FME Server. For the Log file location, click the ellipsis to browse and then navigate to the Temp folder in FME Server Resources. You will need to specify the file name since it does not yet exist, call it IncomingBuildingFootprints.log.

![](./Images/Img4.405.Ex1.LogMessageFilePath.png)

 Click Apply to save this Log configuration.  

![](./Images/Img4.406.Ex1.CompleteLogMessage.png)

<br>**5) Start Automation**
<br>In order for FME Server to start watching the directory for incoming files, the Automation must be enabled. Select the Start Automation button in the top right corner. The button will turn red and an orange warning ribbon will appear across the canvas indicating that your Automation is currently running. This means FME Server is now checking that directory every 30 seconds for updates.

![](./Images/Img4.407.Ex1.StartAutomation.png)

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
As your Automation grows you may wish to turn off Guided mode, this can be done by selecting Hide Guides from the Menu drop-down list.
</span>
</td>
</tr>
</table>

---

<br>**6) Test Automation**
<br>Now let's test the Automation. Locate the source Shapefile datasets in C:\FMEData2019\Data\Engineering\BuildingFootprints. Select a set of files (.dbf, .prj, .shp, .shx) and upload these files into the newly created Resources folder. There are two ways to do this.

You can use the file system (by copying the files to C:\ProgramData\Safe Software\FME Server\resources\data\BuildingUpdates) or use the FME Server web interface.

![](./Images/Img4.408.Ex1.DirectoryWatchDataInFolder.png)

Check back in Resources > Temp, if the log is not yet present select the refresh button until it appears. Click on the file to view the contents and you will see four messages from the Logger showing the individual file paths.

![](./Images/Img4.409.Ex1.ViewDirectoryWatchLog.png)

In fact, every Automation also has a log file recording all the activity that occurs for every aspect of that Automation. To view this return to Automations and this time select the Manage page. This web page lists all existing Automations. Select the Incoming Building Footprints and once within this Automation select Menu > View Log File to view the activity log and spot the recording of these CREATE messages being sent.

![](./Images/Img4.410.Ex1.ViewAutomationsLog.png)

When you view this log file you might also notice reports of the Automation sending Jobs to FME Engine. This is because FME Server is actually performing the Log action using a simple FME Workspace. 

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
Remember, the Poll interval is set up to check the folder only once per 30 seconds - so if the Log file doesn't immediately appear, don't panic! Be patient and it will appear shortly.
</td>
</tr>
</table>

---

Now we know how the Directory Watch Trigger works! We will see in subsequent exercises how to process this information.

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
<ul><li>Create a new Automation</li>
<li>Use Directory Watch to poll an FME Server Resource</li>
<li>Test a Directory Watch trigger by writing to a log</li></ul>
</span>
</td>
</tr>
</table>   
