

Having already set up a solution for incoming email notifications (in Exercise 4b) we can now expand upon that to let the user select a neighborhood in the email subject line. This neighborhood will be used to select a feature to clip the data with.

**1. Open the Starting Workspace**

In FME Workbench open the starting workspace for this exercise.

You must open this workspace as the exercise does not continue on from Exercise 4b. This workspace has more content and is similar to those created in Chapter 3; it reads and resamples raster data, clips it to a boundary, and writes it to a JPEG file.

**2. Add a Text File (TEXTLINE) Reader**

To read information into a workspace, from a notification, requires the use of a Reader. In this case we’ll use a Text File Reader.

Select Readers >Add Reader from the menubar and add a Text File reader using the following settings:

Source Format: Text File

Source Dataset: C:\FMEData2015\Resources\emailIMAP.json

Parameters:Read Whole File at Once: Yes

The Read Whole File parameter is VERY important! Click OK and OK again to add the Reader.

The file being read here is provided because all Readers need a source dataset, but also as an example of what Notification Service sends to a workspace when FME Server receives an email.

Examine the file in a text editor. It contains JSON content. You can see a number of JSON attributes available, which come from an email, and you will be able to read and use any of these in a workspace. In this exercise we’ll be using the Subject of the email.

Because you set the Parameter to read the whole file at once, all of the contents will be read into a single attribute in a single feature, rather than creating multiple features.

**3) Process the JSON Message**

Back in the workspace, connect the Text Line source feature type to the JSONFlattener already in the workspace.

Click the cog wheel icon to open the parameters dialog for the JSONFlattener.

Examine the parameters. This transformer flattens the JSON attributes into FME attributes and exposes all of them.

Browse through the rest of the workspace. It also reads a KML dataset of neighborhood polygons and then filters the neighborhood by the subject of the email to clip by that neighborhood. The UnconditionalFeatureMerger is a custom transformer (available on the FME Store) that simply merges data together without any matching key.

**4) Test the Workspace in FME Workbench**

Test the workspace by running it in FME Workbench.

This will work because the text file contains a sample email where the neighborhood is coming from the email_publisher_subject attribute. If you wish, you can edit the file and use either “Downtown” or “West End” as the neighborhood.

Inspect the output. It should look like this:

**5) Set Writer Path**

Set the JPEG writer path to the Output folder of Server Resources.

**6) Publish to FME Server (Step 1)**

Start the Publish Wizard from the menu or toolbar and enter the connection parameters when prompted. Select the Training repository to store the workspace, as usual.

Click the Select Files button in the dialog and ensure that only the KML dataset VancouverNeighborhoods.kml gets uploaded to the repository.

The easiest way to do this is to click the Files/Folders box to turn off ALL files, and then simply turn the neighborhoods file back on:

Uncheck the GeoTIFF files if they are checked because they are already available in the FME Server Repository.

However, you will still need to point the file location from the workspace to the resource location.
This is necessary because there is no end-user to set this – for example in a published parameter.

Therefore, click OK. A dialog will appear in which you are warned that the file references are not valid. For each of the Orthophoto references, click the […] ellipsis button and browse to the true file location in the resources folder.

When a reference is fixed then it will show as pointing to the resources folder; for example Data/Orthophotos/02-03-HI.tif

Once complete for all files, click OK and then click Next to go on to the next publishing stage.

**7) Publish to FME Server (Step 2)**

In the Services dialog check the Notification Service and click Edit to open the Service Properties.
Choose the topic ImageProcessing you created in the previous exercise as the Subscribed Topic.
The Notification Reader should be set to the Reader (emailIMAP[TEXTLINE]).
This way the content of any incoming email will be passed directly to that Reader.

Click OK and then Publish to complete the wizard.

**8) Send an Email to FME Server**

As before, use any method you like to send an email to your FME Server.
Use the email address you used in Exercise 4a/4b. Enter either Downtown or West End as the subject of the email.

**9) Confirm Workspace Triggered**

Again, if you are using IMAP it make may take a couple of minutes until FME Server is notified.

Open the Web User Interface and click on the Jobs link and to view the Jobs history. Look for a completed job where FME Server ran Exercise4c.fmw in response to the email. Check the Resources/Data/Output directory for your imagery.

Congratulations! Now users can email your FME Server with specific information on how to run a workspace - this is truly Self-Serve! In this next exercise you will configure FME Server to email the user back a result.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. Flibble says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Again, you’ll probably want to unsubscribe Exercise4c from the
ImageProcessing topic if you’re using IMAP. Unless you want all
incoming emails to keep triggering this workspace again and again
and again and again and again and again and again …”
</span>
</td>
</tr>
</table>