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

