# Data Download Service

The Data Download service is the key tool for Self-Serve setups

**What is the Data Download Service?**

When you run a workspace with the Job Submitter service (as in Chapter 2) the data is written to the location specified by the workspace; for example a file, directory, or database.

The Data Download service instead writes the output to a zip file and presents the user with a link to that file. This makes it ideal for self-serve, because the data is delivered directly to the user.

**Creating a Data Download Service**

A workspace becomes available for data download use when the author registers it against the Data Download service when publishing it to FME Server.

**Using a Data Download Service**

Once registered this way, Data Download options become available in the FME Server Web interface for that particular workspace. 

The workspace can be run through the web user interface, or using the developer URL information.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Monsieur D. Server says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
‘Behind the scenes, the Data Download service overrides the
Writer’s destination parameter and writes a zip file to an internal
folder, from where it can serve up the required data to the enduser
in the form of a URL’
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3B </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data
Download</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Scenario</td>
<td style="border: 1px solid darkorange">Airphoto Data Vendor</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">GeoTiff Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create
a
data
download
service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Authoring
for
and
Using
the
Data
Download
Service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3b-­‐Begin-­‐
DataDownload.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3b-­‐Complete-­‐
DataDownload.fmw</td>
</tr>

</table>

This exercise involves making orthophoto data available through a Data Download service. We will also mosaic the various files together and resample them to a lower resolution.

**1. Start Workbench**

Start Workbench (if necessary) and open the starting workspace for this Exercise. You will be familiar with it as it is the same workspace we created in Chapter 2.

**2. Delete Existing Published Parameters**

Some parameters in a workspace are published by default. This lets the user select the output
dataset (for example) when the workspace is run. However, we don’t need to let the user set any
parameters and so best practice suggests we remove them.

Browse the Navigator window and expand the section labelled User Parameters - Published Parameters. Right-click and delete the Feature Types to Read parameter.

Only keep the published parameter for the source dataset.

**3. Add a RasterResampler Transformer**

Now we can add transformers to resample and mosaic the source data.

Click on the connection between the Reader and Writer feature types. Start typing “resampler”. A list of matching transformers will appear. When you see the RasterResampler transformer then select it.

The transformer will now be added into the workspace.

Click the red cog wheel icon on the RasterResampler to open the parameters dialog.

Set the following values to resample the images from 1 metre resolution to 5 metres.

Size Specification: Cell Size

X Cell Spacing: 5

Y Cell Spacing: 5

Interpolation Type: Nearest Neighbor

**4. Add a RasterMosaicker Transformer**

Now repeat step 3, but this time adding a RasterMosaicker transformer between the RasterResampler and the Writer feature type.

Open the parameters dialog as before, but now just click OK to accept the default values.

**5. Modify the Destination Feature Type**

In this scenario, we’ll be writing a single (mosaicked) output file. This is at odds with the current dynamic settings that are part of the workspace.

So, click the cog wheel icon on the Writer feature type to open the properties dialog.

In this dialog uncheck the Dynamic Properties parameter and then type AirphotoMosaic for the Raster File Name.

**6. Publish the Workspace – Step 1**

Save your workspace as Exercise3b.fmw

Start the “Publish to FME Server” process by using the toolbar button or File > Publish to FME Server from the menubar.

Enter the connection and credential settings and click Next. If you cannot remember them, or didn’t save them as your defaults, refer to Exercise 2a for the required values.

For the repository select the Training repository you created in Exercise 2a. Click Next

**7. Publish the Workspace – Step 2**

In the last pane of the publish Wizard check the Data Download Service so that the workspace can be run with this service. You can also leave the Job Submitter Service checked so the workspace can be run via either service.

The default Data Download settings can be used but click the Edit button to review the possible settings anyway.

The Output Dataset parameter is very important if there is more than one Writer in the workspace, as it specifies which is to be output for download. In this case it should be set to the JPEG writer.

Click OK to close this dialog and then Publish to finish publishing the workspace.

**8. Access the Data Download Service**

Now your role switches to that of an end-user who wants to download some data.

Log in to the FME Server Web User Interface. Use the menus and dialogs to navigate to Repositories > Training > Exercise3b.fmw

Notice that you can now run the workspace through either the Job Submitter or the Data Download Service.

Click Data Download.

**9. Run the Workspace**

Once again you are presented with a web form, but this time the form is for running the workspace via the Data Download Service.

As you did in Exercise 2c, scroll down to the Source GeoTIFF parameter and click Browse Resources to browse to the image files you uploaded previously.

Select all of the images (or just a few that neighbor each other).

Click Run Workspace on the bottom right to submit the job via the Data Download Service.

**10. Download the Output**

After a short time a Success page will appear which now includes a Data Download URL link.

Click the link and download the zip file to your computer. Extract the contents of the zip file.

Notice that you have downloaded a single mosaicked JPEG dataset which has been resampled from the original source GeoTiff files.

Congratulations! You have now created a selfserve data download service for airphotos, which can be used by your customers.