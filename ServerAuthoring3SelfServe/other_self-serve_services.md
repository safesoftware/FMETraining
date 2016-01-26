# Other Self-Serve Services

Data Download is not the only Self-Serve Service available.

**Data Streaming**

Whereas the Job Submitter service writes data, and the Data Download service returns a link to the data, a Data Streaming service returns a file of the data itself, streamed back to the client.

For example, the URL for the service can be posted into a web browser, and the data will be automatically downloaded and opened in the application associated with that file type.

Alternatively, the URL can be used directly as the source for a client application. When the client actively downloads the contents on a regular basis – as a GeoRSS reader would – then you have a feed, which is significantly different to a regular data download service.

Data Streaming is a slight misnomer in that a data streaming service does not supply a continuous stream of data; it merely provides a snapshot of the data at a particular point in time.

**What Formats can be Streamed?**

You can use any workspace with the data streaming service, provided it writes data in a format that is file-based or folder-based.

If an output dataset is comprised of more than one file, the service automatically creates a compressed (zip) folder out of the data. For example, AutoCAD DWG format could be streamed, whereas ESRI Shape would be returned in a zipped file.

The most popular formats to stream are those that have a suitable client to read the feed.
Some of the main formats that are output using the data streaming services include:

• RSS

• GeoRSS

• GeoJSON

• KML

• HTML

• JSON

**MIME Types in Workspaces**

A MIME header is a component of a file or e-mail message that is capable of indicating the content type of the file; for example, Content-Type: text/plain indicates a simple text file.

The application that opens a streamed file will depend on the MIME type and file association on the client’s system. MIME type is provided in FME by the first Writer added to the workspace.

The only Writers in FME with a MIME type setting are the TextLine (text file) and Data File Writers.

This parameter only appears when the Writer is added, and (for example) it allows the workspace author to set a MIME type of HTML and therefore stream data directly into a web browser.

**KML Network Link**

A KML Network Link service is when the output from an FME Server translation is a simple KMZ (zipped KML) file that contains solely a network link to reference the workspace on the server.

Whenever a KML browser (such as Google Earth) opens this dataset it follows the link, triggering FME Server to run the translation and return the true output data.

Because Google Earth permits a refresh rate for network links, the translation can be re-run at a user-defined interval. This way the results are always as up-to-date as the chosen interval.

Of course, in this scenario the output is never written to a permanent dataset; the resulting data is simply streamed to the browser, which writes it to a cache.

As with other services, a workspace becomes available for use as a KML Network Link service when the author checks the KML Network Link checkbox in the FME Server Publishing Wizard.
The edit button provides a whole series of different parameters that control the refresh rate when the data is opened in Google Earth.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3G </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data
Streaming</span>
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
Data
Streaming
Service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Data
Streaming</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3g-­‐Begin-­‐
DataStreaming.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3g-­‐Complete-­‐
DataStreaming.fmw</td>
</tr>

</table>

Any exercises we’ve completed up until now could also be used with a simple Data Streaming service, just as easily as a Data Download service, and with very little editing.

This would allow customers to preview their downloads in a browser.

**1. Open Starting Workspace**

Start Workbench and open the starting workspace. Alternatively open the workspace from any of the previous exercises.

**2. Add Writer**

For data streaming it’s important that we have a workspace with a JPEG writer, not Generic.
Even if the Generic writer writes a JPEG file, it can’t be streamed because the MIME type is unknown.

So, use Writers > Add Writer from the menubar. When prompted add a Writer as follows:

Writer Format JPEG (Joint Photographic Experts Group)

Writer Dataset C:\FMEData2015\Output\Training

Ensure Copy from Reader file definition is selected. Click OK to close the dialog. Open the Feature Type Properties dialog, change the Raster File Name to AirphotoPreview, and make sure that the fanout option is unchecked.

Click the Format Parameters tab and check the parameter for World File Generation. It needs to be set to “No”. If it is not “No” then multiple files will be output and streaming will fail.

**3. Publish the Workspace to the Data Streaming Service**

Connect the newly created Feature Type to the RasterMosaicker Output port. Then select File > Publish to FME Server from the menubar to publish the workspace.

Save the workspace (as Exercise3g.fmw) and publish it to the Training repository again; but this time, register it with both the Data Download and Data Streaming services.

For the Data Download service, click the Edit button to make sure the Output Dataset associated with the service is the Generic Writer.

For the Data Streaming service, click the Edit button to make sure the Output Dataset associated with the service is the JPEG Writer, and only the JPEG writer.

**4. Run the Workspace in the Data Streaming Service**

Acting as a user now, go to the Web User Interface and navigate to your workspace: Workspaces > Training > Exercise3g.fmw > Data Streaming

Enter some parameters. Data Download specific parameters like destination coordinate system and output format will not apply when streaming.

Click Run Workspace on the bottom of the form.

After a short time, the resulting image will appear on the webpage. Your browser automatically displays the image because FME Server provided the MIME type image/jpeg in the headers of the page it returned.

Hopefully you see how this service could be incorporated into your self-server data sharing solution, so users can preview the data they want to download at lower resolutions first.

Congratulations! You have now created a Data Streaming service for your customers.