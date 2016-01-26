# Running a Workspace on FME Server

This section introduces running a workspace on FME Server

Once a workspace is uploaded to FME Server, it can be run on that server. There are several ways to run a workspace, the simplest being using the Job Submitter service.
This service can be accessed either through the Web User Interface or via a URL

Running the Job Submitter using the Web Interface Using the web interface to run a workspace is very similar to running it in FME Workbench; you simply locate the workspace and click a Run button.

To locate a workspace first click on Workspaces or the Run Workspace entry in the main menu of the web interface.

Secondly, click on the repository that contains the workspace to be run.

Next, click on the workspace itself.

Finally you have the option to click which service to configure or run.

**Configuring a Translation**

Clicking on a service for a workspace is the equivalent to the Prompt and Run option in FME Workbench. You get to define what parameters are going to be set for the translation, such as File to Upload, Source File and Output Coordinate System.

For example, here the user can specify where the source data is available:

If data was made available using Resources functionality, then the user could choose the Browse option to search for and select it:

Once the parameters are set, click the Run Workspace button to complete the process.

**Running the Job Submitter using a URL**

All job requests to an FME Server are a variation on an HTTP request. This makes running a workspace via a URL very simple, provided you know what form the request will take.

The easiest way to find that URL is through the workspace services in the FME Server web interface.

Notice that the service configuration dialog includes a section labelled “Developer Information”.
Once expanded, an example URL and example form are displayed.

The URL shown uses a HTTP GET request whereas the HTML form uses a HTTP POST request.

This information is a useful tool for building your own web applications that access FME Server services, because you can copy the HTTP request and embed it on your own website or application.

You could also embed the URL or form into an email, or paste the URL directly into a web browser.

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
There are limits to the amount of data you can send in a GET request because URLs
have length restrictions that vary depending on the browser being used. If you
anticipate that your request parameters may include very long strings, use a POST
request.
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2C </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Running a Workspace</span>
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
<td style="border: 1px solid darkorange">Run the previously published workspace</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Running a workspace on FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">Exercise2a.fmw
(in
the
Training
repository
on
FME
Server)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">Exercise2a.fmw
(in
the
Training
repository
on
FME
Server)</td>
</tr>

</table>

Now we have both a workspace and data on the server, we can run the workspace to translate the uploaded data.

**1. Browse to the Workspace**

Open the Web User Interface in a web browser (if it isn’t already) and click Workspaces on the upper right-hand menu. A list of available repositories now appears.

Click on the Training repository in the list; this was the repository we created when we published the workspace. This will cause a list of available workspaces in that repository to be displayed.

Now click on your workspace, Exercise2a.fmw, and then Job Submitter. The Job Submitter parameters will open, which will allow the selection of specific source files.

**2. Select Source Data from Resources**

The Configure page allows you to set any published parameters for a workspace, in the same way that using “Prompt and Run” would in FME Workbench.

Parameters which represent file sources are given special treatment to allow you to either Browse to a Resource dataset, Upload data or Specify Location of the data as a path on the file system.

Having already uploaded data to a Resources folder, we will browse to those files.

Select Browse Resources and expand the Data and Orthophotos folders. Select all or some of your files. The other parameters can be left with their defaults.

**3. Select Destination Folder**

Once the source data is selected, we can now select an output location in the Resources folder.

Locate the Destination Dataset parameter and click the Browse tab if it is not already highlighted. Select the Data folder, click New Folder and create a new folder called Output.

Ensure that the Output folder is selected as the output location.

*NB: Writing to a resource folder like this is important for when there is no local or network path for FME to write the output to.*

**4. Run the Workspace**

Once you have selected some image files, click Run Workspace at the bottom-right of the configure page. This will submit the job with your parameters and an FME Engine will run the workspace.

The browser will wait until the job completes because it was submitted in mode known as synchronous. After a short time a Success message will appear with links to view or download the FME log file.

**5. Locate Output**

When complete, browse to the Resources (Manage > Resources) section of the interface and look in the Output folder. You should see the result of the translation written to this folder.

**Congratulations!**

You have now run a workspace with the Job Submitter service on FME Server.

**Advanced Task**

You can submit a job to the FME Server Job Submitter Service or any other service using a URL or by posting a form. The syntax is provided in the Configure page for your workspace, so let’s give it a try.

**1. Browse to the Workspace**

Browse to your workspace again in the Web User Interface using Workspaces > Training > Exercise2a.fmw > Job Submitter.
At the bottom-left corner of the page, expand Developer Information

**2. Run the Workspace**

The Developer Info button opens up a section that shows how to run the workspace using a Direct URL (as a HTTP GET) and a web form (using HTTP POST).

Copy the Direct URL and paste it into the address bar of a new tab in your browser. Press enter to activate the URL and run the workspace.

You may be prompted to authenticate again in which case enter the same user and password as you did in Exercise 2a. The job will be submitted synchronously again although the results page will look different since it was not submitted via the web interface.

**3. Change Parameters**

Examine how the published parameters are set in the URL and try to change one of the source GeoTiff file names (to different ones in your Resources) before running the workspace again.