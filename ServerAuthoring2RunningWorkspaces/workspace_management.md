# Workspace Management

Because Workbench is a client of FME Server, workspaces may be transferred to and from an FME Server repository.

**Transferring Workspaces**

FME Workbench has the ability to:

• Publish a workspace to FME Server
• Republish a workspace to FME Server
• Download a workspace from FME Server

These three capabilities are accessed in FME Workbench either through the menubar…


…or the toolbar:


<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Professor Lynn Guistic says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Published workspaces are held on FME Server in a file-based
repository. Each FME Server may have multiple repositories, but any
workspace can only belong to one of them.
All metadata related to the workspace is held separately in FME Server’s
repository database. This metadata includes information about source
and destination datasets, workspace feature types, and published
parameters.”
</span>
</td>
</tr>
</table>

**Publishing a Workspace**

Once a workspace has been authored it is “published” to FME Server. A workspace is published using a simple wizard interface that connects using the FME Server REST API.

**Connecting to Server**

The first dialog in the publishing wizard is where a connection is defined.

Workbench can connect to FME Server by web connection (using HTTP and the REST API).
The web connection requires the URL of the Server. HTTP is used when the FME Server is not on the same Local Area Network, but on a web-accessible server.

The dialog also provides fields in which to define connection credentials. Note the ability to save time by reusing Windows session credentials

**Repository Selection**

The next dialog defines the repository for the workspace:

Either an existing repository can be used, or a new one created. The workspace name can also be edited, though it must always conclude with “.fmw”.

**Workspace Registration**

The final dialog defines which services the workspace is to be registered against.

The Job Submitter service allows FME Server to run a workspace as-is. This is the closest to running a workspace on FME Desktop. All inputs and outputs are defined in the workspace so data is simply written out and not streamed or delivered in any other manner.

Job submission is ideal for testing workspaces, and for running large-scale and batch translations that make use of the server process queue.

**Republishing a Workspace**

Once a workspace has been published, the republish tool becomes active.
Further updates to the workspace (within the same session) can then be uploaded with a single click:

The same parameters are used as before. If changes need to be made to these parameters, then the full publishing wizard should be used.

**Downloading a Workspace**

Workbench can also “download” a workspace held in an FME Server repository. This is usually done in order to make edits to the workspace. Note that downloaded workspaces are copies of the original, which remains in the FME Server repository.

The downloading wizard begins with the same connection dialog as the publishing wizard. From there, the second – and final – dialog page is a repository and workspace selection tool:

The user is then prompted for a location to save the workspace. The default is <user>/FME/My FME Server Workspaces. The workspace – and resources – are then downloaded.

Once downloaded, the workspace is automatically opened within Workbench for editing.

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
To avoid entering the same parameters every time a connection is made, set the
parameters, click the Defaults button, and select ‘Save as My Defaults'. Now these
parameter values will be used automatically every time the connection dialog is opened.
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Besides workspaces, it’s also possible to publish/download FME custom
transformers and custom formats to/from a server repository.”
</span>
</td>
</tr>
</table>

**Repositories**

Repositories are storage facilities for FME Server workspaces.

You can think of each repository as being like a folder on a file-system. Like a folder, it stores workspace files. Also like a folder, access rights can be granted to individuals and groups.

Repositories can be accessed through the web user interface using the Run Workspace button on the main menu:

Although the workspaces are stored on the file-system (C:\apps\FMEServer\Server\repository) information about each workspace is stored in an internal database within FME Server.

For interested experts, the FME Server core communicates with the database via JDBC over TCP/IP.

The contents of this database should never be edited directly.

Querying the database is permissible, although extracting repository information is more commonly achieved using the REST API.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police Chief Webb-Mapp says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Security in FME Server is very important, and
never more so than for repositories.
For each repository you create, check the
security settings. If you don’t then end-users
may not get access to the repository!”
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2A</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Publishing a Workspace</span>
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
<td style="border: 1px solid darkorange">Create a workspace, publish it to Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Publishing a workspace to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting
Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished
Workspace</td>
<td style="border: 1px solid darkorange">C:\
FMEData2015\Workspaces\ServerAuthoring\Exercise2a-­‐Complete.fmw</td>
</tr>

</table>

This simple exercise will refresh your memory on FME Workbench and demonstrate how to publish a workspace. In this scenario you are an FME user working for a company producing and selling airphotos. You want to publish a workspace to FME Server to translate GeoTiff datasets to JPEG.

**1) Generate Workspace**

In the FME Workbench start screen, select the option to Generate Workspace

Alternatively you can select File > New > Generate from the menubar or use the shortcut Crtrl + G.

When prompted, set up the workspace using the following parameters:

Reader Format GeoTIFF (Geo-referenced Tagged Image File Format)
Reader Dataset C:\FMEData2015\Data\Orthophotos\06-07-LM.tif
Writer Format JPEG (Joint Photographic Experts Group)
Writer Dataset C:\FMEData2015\Output\Training

Before clicking OK, select the option for Dynamic Schema at the bottom of the dialog.

This will allow the workspace to process any GeoTiff file, not just the one originally chosen.

**2. Save and Run Workspace**

Save the workspace as Exercise2a.fmw (using File > Save from the menubar) and then run it (using Run > Run Workspace). Browse through the file system to confirm that you have written a JPEG file to the output directory.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Professor Spatial says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“You should always run your workspace first in Workbench, before
publishing it to FME Server.
This is the easiest way to ensure the workspace functions as expected. If it
fails in Workbench, it won’t suddenly work on FME Server!”
</span>
</td>
</tr>
</table>

As a further test, run the workspace a second time but this time using Run > Prompt and Run.
This action prompts you to select the source and destination datasets, instead of simply using those defined in the workspace.

Select a different file this time (say, 08-09-NO.tif) and open the output to prove that the contents are different to before.

**NB:** If you missed setting a Dynamic Schema in step 1, you can either recreate the workspace (it will only take a minute) or – if you know how – open the Reader feature type properties dialog and set a merge filter.

**3. Publish Wizard (Step 1)**

Workspaces are published to FME Server using a wizard.

Choose File > Publish to FME Server from the menubar (or select the same tool on the toolbar).

In the first dialog of the wizard you are prompted to enter connection parameters to FME Server.

Enter the parameters provided by your training instructor.

In most cases the parameters will be as follows:

FME Server URL: http://localhost

Username: admin
Password: admin

Click Next to continue. If the credentials are correct a connection will be made and you will move on to the next dialog in the wizard.

**4. Publish Workspace (Step 2)**

The next dialog prompts you to choose a repository in which to store the workspace.

For this exercise we’ll create a new repository by clicking the New button. When prompted enter the name Training.

Click OK to close the Create New Repository dialog. Uncheck the box labeled Upload Data Files, and then click Next to continue the wizard.

**5. Publish Workspace (Step 3)**

In the final screen of the wizard we can register the workspace for use with various services.

Select the Job Submitter service as this is the only service we are using for now and click Publish to complete publishing the workspace.

After a workspace is transferred to Server, the log window displays a message reporting which workspace has been published to which repository and for which services.

In this exercise, the workspace Exercise2a.fmw has been published to the Training repository for use in the Job Submitter service.

Congratulations! You have now created a workspace and published it to FME Server.

**Advanced Task**

Open the FME Server Web User Interface in a web browser and log in using the same connection parameters as you published the workspace with.

Click Security on the main menu to open security settings, and then click the Object Policies tab.

Locate the Training repository in the list of security objects. You should see that the roles allowed to make use of it is restricted to the one(s) to which the publisher’s account belongs.

In this case the user was admin, which is associated with the fmeadmin role. Therefore only an administrator will be able to make use of the repository that we have just created.

Click on the repository object to open its security policies. Add the fmeguest role so that users with a guest account can access this repository.

If you created a guest account (WebGuest) in Exercise 1b, then log out and log in again using that account, to prove that guests now have access to the repository.

