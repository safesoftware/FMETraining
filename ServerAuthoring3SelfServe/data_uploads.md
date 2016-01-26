# Data Uploads

Data Upload is a good way for a user to provide data to be
processed

**What is Data Upload?**

As the name suggests, Data Upload allows a user to deliver data to FME Server for processing.

Data Upload can be used from any FME Server client, including:

• The Web User Interface
• An FME workspace
• A custom web application

Data Upload is often used for submitting data to an organization, for example a property developer submits a planning application containing a DWG dataset to a municipal planning department.

It is also often used for publishing data to be processed on FME Server, for example where FME Server is set up as a data validation web service and an end-user is uploading a set of data to be checked.

It’s worth noting that data upload also includes other resources that may be required for a translation to run; for example custom transformers or text-file lookup tables may also be uploaded.

**Implementing Data Upload**

In FME, there are two forms of data upload: the Data Upload Service and the Resource Folders.

The Data Upload Service allows data to be uploaded to a particular workspace in a particular repository. The data is held temporarily for the workspace to be run.

The Resource Folders allow data to be uploaded to a folder for use by any workspace in any repository. This upload is persistent and the data held there for as long as it required.

**The Data Upload Service**

The Data Upload Service allows data and other resource files to be uploaded to FME Server.

Files can be uploaded through the FME Server Publishing Wizard, when a workspace is published from Workbench to FME Server:

Clicking the Select Files button opens a dialog that shows what data is being uploaded.

The upload of these files can be turned on and off as required, and you can also change the location to which data is uploaded – either to a repository (Data Upload) or to a Resource Folder – by clicking the Change Location button.

The other way to upload data with this service is through the configure dialog when running a workspace.

Use the File Upload section to upload the data, then choose Select From Recently Uploaded Files to select which files should be assigned to which published parameter:

Be aware that data uploading with this service is only available with the chosen workspace. Also, the data is stored only temporarily and will be deleted in – by default – 30 minutes time.

**Resources Folders**

Resource Folders are a more permanent and flexible way to upload data and resources to FME Server. Similarly to the Data Upload Service, files can be uploaded at the same time as a workspace.

When editing the resource info (in the publishing wizard, under Select Files, Change Location) you would simply choose to upload the files as a shared resource (left). One other requirement is to select a location on the resources file system.

Another way to use this functionality is to use the Resources tool in the FME Server Web User Interface (below). Here you can upload, download, copy, move, and delete files; plus manage folders too.

**Resource Upload**

To upload data simply click on a folder and then choose the Upload option:

The upload tool gives you the option to either upload a set of files, or an entire folder of data:

To upload a folder of data requires use of a browser – for example Google Chrome – that has folder upload capabilities. At the time of writing, neither Firefox nor IE has this ability.

**New Folder**

The New Folder tool creates a new folder or sub-folder in the Resources mechanism.

For example, to create a subfolder in the Data folder simply click on Data and then click

**New Folder:**

You are prompted to enter a name for the new folder.
Enter a name, click OK, and the folder is created.
Besides those methods, folders in the Resources mechanism can be accessed – or created – in the server’s file system.

For example, here are folders in C:\apps\FMEServer on a Windows file system.

**Benefits**

Resource Folders are more permanent because the data is not automatically deleted after a set time. Instead all uploaded files reside there until removed by a user/administrator.

Additionally, Resource Folders are more flexible for a number of reasons.

Firstly, you can access the files and manage them through a file system on the server. This is useful in itself, but it also allows the data to be accessed through UNC paths, which the Data Upload service does not.

Secondly, Resource Folders can be used for more than data upload.

It’s also possible to write the results of a translation to a resource folder, as in this example. You would just set the output dataset parameter to a resource folder.

Also, files inside a Resource Folder can be managed using the REST API too, with POST and GET functions for downloading files, creating folders, and copying files (for example). This gives control over these resources to any developer who wishes to create their own web applications.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3A</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data Upload</span>
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
<td style="border: 1px solid darkorange">GeoTiff Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a data upload service for validating spatial data</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Authoring for and Using the Data Upload Service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting
Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished
Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3a-­‐Complete -­‐
DataUpload.fmw</td>
</tr>

</table>

This time you wish to create a solution for data providers to automatically upload data to your system. Naturally you will wish to test data quality – in this case resolution – and reject any data that does not meet your standards.

**1. Start Workbench**

Start Workbench (if necessary).

**2. Add Reader**

The first component required for Data Upload is a Reader, so select Readers > Add Reader from the menubar. When prompted add a Reader with the following parameters:

Reader Format GeoTIFF (Geo-referenced Tagged Image File Format)
Reader Dataset Any TIF file in C:\FMEData2015\Data\Orthophotos\
Workflow Options Single Merged Feature Type

The workflow option is important because setting a merged feature type allows any TIFF file to enter the workspace. If it is not set then only the original file could ever be read.

**3. Add RasterPropertyExtractor**

To test the quality of the incoming data we need to first extract some information about it. So, add a RasterPropertyExtractor transformer. You can do this by clicking on a clear part of the canvas and typing RasterPropertyExtractor. Drag a connection from the Reader to the transformer.

This will extract information about the incoming data and store it as attributes.

If you wish, you may connect a Logger transformer and run the workspace, just to see what the attributes look like.

**4. Add Tester**

Now we will add a Tester transformer to test whether the properties of the data are a match for what we require.

Do this by clicking on the RasterPropertyExtractor transformer and typing Tester. Then select Tester from the drop-down list of transformers.

The workspace will now look like this:

**5. Set Tester Parameters**

Click on the red cogwheel icon on the Tester to open its parameters dialog.

In the dialog double-click in the Left Value field. From the drop-down list select Attribute Value > _num_bands. This attribute tells us how many bands are in the source data:

Set the Operator field to equals (=) and type the number 3 into the Right Value field:

Now repeat that process to test for _spacing_x = 1 and _spacing_y = 1

Finally, set the Pass Criteria parameter to All Tests (AND). If you don’t then the incoming data will pass even if only one aspect of it is correct.

Click OK to close the dialog. We now have a test to ensure the incoming data has the correct number of bands and the correct resolution.

**6. Add AttributeCreator Transformers**

We now have to decide how we are going to communicate the results of the translation to the end-user. The most effective way is perhaps to respond with a web page describing the results.

To generate some very simple HTML, we’ll use an AttributeCreator transformer. So add an AttributeCreator transformer and connect it to the Tester:Failed port:

Now open the parameters for the AttributeCreator. Enter an attribute name of text_line_data (the name is important as we’ll see shortly) and for the value click the […] button to open a text editor.

In the text editor, just enter some simple HTML such as:

<html>
<p>Data QA Test Failure</p>
</html>

Click OK and then OK again to close the dialogs.

**7. Duplicate AttributeCreator**

Having created HTML for a failure we now need to do the same for a successful test. The simplest way to do this is select the existing AttributeCreator and press Ctrl+D to duplicate it (alternatively you can use Right Click > Duplicate).

Connect the new transformer tothe Tester:Passed port.

Now open the parameters dialog and change the message inside from Failure to Success.

**8. Add Writer**

To output HTML in a way that will open automatically, we need to stream it through a Text File writer. So, select Writers > Add Writer from the menubar.

When prompted create a Writer as follows:

Reader Format Text File
Reader Dataset C:\FMEData2015\Output\Training\output.html
Parameters
MIME Type text/html

Really the output dataset is irrelevant here as it will never be used. The MIME type is set by clicking the Parameters button and using the setting inside that dialog.

Click OK and OK again to close the dialogs and add the new Writer.

**9. Connect Writer**

Connect the Writer into the workspace by dragging connections from the output ports of both AttributeCreator transformers:

If you expand the text writer’s attribute list you’ll see it is expecting data to arrive in an attribute called text_line_data, which is why it was so important that the AttributeCreators create their attribute with that exact name.

**10. Delete Existing Published Parameters**

The workspace is now complete except for one thing, published parameters. Remember these are how the user is prompted to make a selection to control the translation.

In this case we wish for the user to be given the chance to upload data, but not anything else.
However, if you look in the Navigator window of Workbench you’ll see that some parameters in a workspace are published by default.

The source parameter is great, as it will let the user upload a source dataset; but the other parameters are not required. They will confuse the user and have no effect on the translation.

So delete these two parameters. You can either click them and press the delete key, or right-click them and select delete.

**11. Test Run Workspace**

Test run the workspace in FME Workbench to ensure it runs to completion. It will create a HTML file as output, though it won’t open it automatically because only FME Server can do that.

**12. Publish to FME Server**

Save the workspace as Exercise3a.fmw. Then select File > Publish to FME Server from the menubar to start the publishing process.

As before (in Chapter 2) enter your connection parameters and then select the Training repository as the location to store the workspace. However, in that dialog be sure to uncheck the box labelled “Upload data files”. The end-user will be uploading the files; we don’t need to.

For the Service to register against, uncheck Job Submitter (and any other services) and check Data Streaming. We’ll cover Data Streaming in more detail later in this chapter; for now just click Publish to finish publishing the workspace.

**13. Run Workspace**

Now – in the role of a data supplier – open the FME Server Web Interface in a web browser.

Browse to the newly uploaded workspace (Workspaces > Training > Exercise3a.fmw) and click Data Streaming:

In the configuration page, under File Upload select Browse and add the file C:\FMEData2015\Resources\Self-Serve\GoodData.tif. It will then be uploaded to FME Server and become available for use.

This is the key part of the process: the ability for an end-user to upload data to process.

Under Source GeoTIFF File(s), choose Select From Recently Uploaded Files for the source GeoTIFF data and select the newly uploaded GoodData.tif 

Notice there are no other published parameters as there is nothing else we wish the end-user to have control over.

Now click the Run Workspace button. The translation should run to completion and a brief message given to alert us to the status of the dataset.

You can now run the same process on the file BadData.tif to prove that it fails the tests.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
‘Yes, the output from this exercise is sinfully basic, but we’re not here to
teach you HTML! Now you know how to create a Data Upload service
from the FME Server side you can apply your web skills to producing a
more aesthetic result – and even a custom form for uploading the data.
Additionally, you can add extra tests and functionality inside the FME
workspace in order to carry out more QA. The GeometryValidator
transformer is a great solution for dealing with vector data.’
</span>
</td>
</tr>
</table>