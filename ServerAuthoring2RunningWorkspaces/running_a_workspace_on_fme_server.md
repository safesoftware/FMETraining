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

