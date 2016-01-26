# Automated Data Processing

Automated Data Processing is an unscheduled, but automatic, workspace process.

**What is Automated Data Processing?**

Automated Data Processing is when a workspace is run in response to an event, rather than on a schedule. Because the time of the event cannot be predicted, the workspace is not run at a set time. It is automatic, but unscheduled.

**Setting up Automated Data Processing**

There are two common methods by which to automate FME Server in response to an event:

• Notifications

• REST API

**Automated Data Processing with Notificiations**

If you’ve just finished Chapter 4 – which covered notifications – the most obvious way to set up Automated Data Processing will be through a notification.

In this scenario, a Publication is set up to trigger a topic. The workspace is tied to the topic so that it is run as the topic is triggered.

Although the workspace can also send an outgoing notification, here we’re concentrating on the idea of starting the workspace, not what it does.

Here we aren’t really talking about events that need to be processed; this is more the case that a given event starts a larger processing task.

For example, a system administrator might send an email to FME Server to inform it a daily update of database tables is ready to run. The content of the email isn’t important, just the fact that it is triggering a translation.

In this way a workspace can be started through protocols such as Email, Directory Watch, or JMS.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mrs. Dee B. Emess says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“You can set up a trigger to call FME Server for each individual
addition/edit to a record, or you can use a Bulk Mode, which is
useful when a large number of edits are made that can be
processed by a single workspace.
FMEpedia has some great examples of Single and Bulk processing
for Oracle, SQL Server, and PostGres/PostGIS.”
</span>
</td>
</tr>
</table>

**Web Automation Services**

Web Automation Services are those such as IFTTT and Zapier, which tie together different webbased applications using conditional statements.

Such services allow you to define a statement using a trigger (the  If part) and an action (That).

For example, here is a pre-defined IFTTT “recipe” to send an email when congress is about to vote on a bill.

Typically intended to support tools like Gmail, Dropbox, and Facebook; it’s also possible to connect FME Server into a workflow like this.

For example, a Zapier “zap” looks like this:

Here, whenever a tweet with a specific keyword and location is discovered, a workspace is run on FME Server.

In this example the search term is for the word “earthquake” and the location is defined (not shown here) as within 50km of the city of Vancouver, BC.

The FME workspace being run is called EarthquakeResponse.fmw and the Text File Reader within it is being fed the coordinates of the tweet:

Now Zapier will check for such a tweet (by default every 15 minutes) and run the workspace on FME Server in response:

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5B </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Automated
Data
Processing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Scenario</td>
<td style="border: 1px solid darkorange">Airphoto
Data
Vendor</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">GeoTIFF
Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Run
a
translation
workspace
whenever
new
data
is
added</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Automated
Scheduling</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5b-­‐Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5b-­‐Complete.fmw</td>
</tr>

</table>

As a member of the Airphoto Data team, you would like to have FME start processing data once an update becomes available, and an email to be sent to alert you of this. Availability of new data will be denoted by new files in a folder. The Directory Watcher protocol can be used to do this.

**1. Create New Topic**

In the Notifications dialog create a new Topic called NewData.

**2. Create a New Publication**

Now create a new Publication. Use the following settings:

Publication Name: New Data Watcher 

Topic to Publish to: NewData (the topic you created in step 1)

Protocol: Directory Watch

Directory to Watch: Browse Resources \Orthophotos and check it

Filter: Create (remove Modify and Delete)

**3. Open Workspace**

In FME Workbench open the starting workspace. This workspace will read the raster data using a FeatureReader transformer. It will then write the data out. Notice the workspace also creates an email to send as an output notification.

**4. Add a Text File (TEXTLINE) Reader**

Select Readers >Add Reader from the menubar to add a Text File Reader. This Reader is necessary to receive the incoming information from the Directory Watcher. Use the settings:

Reader Format: Text File

Reader Dataset: C:\FMEData2015\Resources\NewFile.json

Parameters:

Read Whole File at Once: Yes

Click OK and then OK again to add the reader. Don’t connect it to anything in the workspace.

This JSON file is provided as example of what the Notification Service sends to a workspace when the Director Watcher picks up a change to the directory. You can examine the JSON file in a text editor to see how the message is structured.

**5. Add JSONFlattener**

Add a JSONFlattener transformer and connect it to the Text File feature type.

Edit the properties of the transformer as follows:

JSON Attribute: text_line_data

Recursively Flatten Objects/Arrays: Yes

Prefix New Attribute Names With: <Leave blank>

Attributes to Expose: Type in the following two entries onto two lines:

fns_type

dirwatch_publisher_content

**6. Format the File Name for Joining**

The attribute dirwatch_publisher_content now looks something like this:

ENTRY_CREATE C:\apps\FMEServer\Data\\Orthophotos\10-11-JK.tif\n

We need to format this attribute in order to extract the file path.
Add a SubstringExtractor transformer, to the Tester Passed port 

Open the parameters dialog and set the following:

Source Attribute: dirwatch_publisher_content

Start Index: 13

End Index: -1

Result Attribute: Path

**7. Read the New File**

Connect the SubstringExtractor transformer to the FeatureReader that already existed in the workspace.

**8. Set FeatureReader Parameters**

Open the FeatureReader parameters dialog. Ensure that the Reader Format is set to GeoTIFF and that the Dataset File parameter is set to the value of the Path attribute:

**9. Set the Email Address**

In this case the emails will only go to you or another manager so you can set a fixed email address. Open the parameters dialog of the FMEServerEmailGenerator and enter your address in the To: field.
Change the subject and message fields as well so they tell you this is new data and not a data order.

**10. Publish the Workspace (Step 1)**

Start to publish the workspace to FME Server. As usual use the same connection parameters and select the Training repository.

Uncheck the Upload Data Files checkbox to ensure that no files will be uploaded to the repository and click OK and Next.

**11. Publish the Workspace (Step 2)**

In the Services dialog check the Notification Service. Open the Service Properties dialog and choose the Topic NewData that was created earlier.

Make sure the Notification Reader is set to your NewFile[TEXTLINE] Reader only.

In the same Edit Service Properties dialog expand the Notify on Job Completion settings and set Topics to Publish (Success) to the sendemail topic created in a previous exercise.

The Notification Writer should be set to your Email[TEXTLINE] writer.

Leave Topics to Publish (Failure) blank, but notice this is where you could handle a failure in the workspace if you needed to.

Click OK and Publish to complete the wizard.

**12. Add some New Data**

Use the Web User interface to add a new orthophoto file to the Resources folder.

To do so, click the Manage Menu > Resources and expand the Data > Orthophotos folder. Browse to the folder C:\FMEData2015\Data\Orthophotos and select another GeoTIFF file for upload, for example 08-09-PQ.tif

After a few minutes you should receive an email with the resampled image attached.

**Congratulations!** You have created a solution that automatically processes new data files and alerts users to their presence through an email notification.