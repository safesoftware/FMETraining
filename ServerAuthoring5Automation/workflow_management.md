# Workflow Management

Workflow Management is great for controlling workspaces in sequence or branching with in-built logic

**What is Workflow Management?**

Workflow Management is a technique where a set of workspaces can be run in a particular sequence, and where branching can take place to run one workspace or another depending on the result of a set of pre-defined decisions.

Workflows like this are set up using a control (parent) workspace, which defines the logic for any decisions that needs to be made, and runs subsequent (child) workspaces according to that logic.

Implementing Workflow Management

A master workspace calls other workspaces by using one of a number of transformers. For FME Server the most commonly used transformer is the FMEServerJobSubmitter.

Here a control workspace is using the FMEServerJobSubmitter to run three further FME workspaces. Maybe each workspace is a separate step in a database update process.

If a particular task fails then the output is routed to a text file Writer – meaning this could be used in a notification system to send an email to an administrator alerting them to the failure.

If there are several workspaces, but only one of which should be run, then the logic for deciding which one can be made using a Tester, or other filter transformer.

For example, here an organization runs a daily process to upload field updates into a database.
However, once a week the process needs to carry out extra actions; such as archiving the source files to Dropbox, or exporting the database contents to Shape files for use by another team.

Each process is defined in a separate workspace, which is called by an FMEServerJobSubmitter transformer.

The Tester transformer prior to the FMEServerJobSubmitters contains the logic over which process is to be carried out. For example it may be testing which day of the week it is. 

If it is Monday to Thursday then the test passes and it will run the usual daily update process. If it is a Friday then the test fails and it will run the weekly update process with the extra tasks.

Again, text file writers are being used to record the result of the translation and whether it was a success or failure. If necessary these could be used to send notifications to a system administrator.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Monsieur D. Server says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“The Control Workspace may start with a Reader that reads a
source dataset, where each source feature triggers the job
submitter. For example, the source data may be a list of files that
are to be translated.
But more often just a single feature is needed to trigger the child
process once. In this case a Creator transformer can be used
instead of a Reader.”
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5C </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Workflow Management</span>
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
<td style="border: 1px solid darkorange">Chain
Three
Workspaces
Together</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Workflow
Management</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Begin-­‐Data-­‐Load.fmw

C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Begin-­‐Data-­‐Process.fmw

C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Begin-­‐Data-­‐Rasterize.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Complete-­‐Control1.fmw

C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Complete-­‐Control2.fmw

C:\FMEData2015\Workspaces\ServerAuthoring\Exercise5c-­‐Complete-­‐Control3.fmw</td>
</tr>

</table>

This example shows how to chain together 3 separate workspaces into a complete workflow. The
workflow loads data, performs a join and then creates web map tiles in three separate steps.

**1. Publish Workspaces**

The three workspaces that are to be chained together already exist and need to be published to FME Server. So create a new repository called workflow_management and publish the following three workspaces:

• Exercise5c-Begin-Data-Load.fmw

• Exercise5c-Begin-Data-Process.fmw

• Exercise5c-Begin-Data-Rasterize.fmw

They can simply be published with no resources and registered only with the Job Submitter.

**2. Create Control Workspace**

Now we can create a control workspace to manage the three child workspaces.

Start with an empty canvas in Workbench and add a Creator transformer. A Creator will simply create a single non-geometry feature that can be used to trigger the rest of the workspace.

Now add an FMEServerJobSubmitter transformer after the Creator: 

Save the workspace as workflow_management_controller.fmw

**3. Add Published Parameters**

Published Parameters are how information can be passed from a master workspace to a child workspace. The child workspace has existing parameters and new ones can be created in the master in order to receive information that is to be passed in.

The first child workspace (for loading data) has two Readers to read two input datasets; therefore we can specify the source data using published parameters.

In the Navigator window locate the section named Published Parameters.
Right-click on Published Parameters and choose Add Parameter.
Create two new parameters:

A. Type: Filename (Existing)

Name: voting

Prompt: voting:

Configuration: Description: shapefile,

Filter: *.shp

B. Type: Filename (Existing)

Name: properties

Prompt: properties:

Configuration: Description: shapefile,

Filter: *.shp

**4. Set FMEServerJobSubmitter Parameters**

Open the parameters dialog for the FMEServerJobSubmitter. Here we can define the workspace that is to be run by this master process.

Enter the usual connection parameters. 

For the workspace to run choose the workflow_management repository and from there select the workspace Exercise5c-Begin-Data-Load.fmw.

Click Next to continue.

Set Wait for Server Job to Complete to Yes.

For the first published parameter, click the drop-down arrow (to the right) and choose User Parameter > voting

For the second, click the drop-down arrow and choose User Parameter > properties 

Click Finish to close the parameters dialog.

**5. Add Logger Transformers**

Right click the FMEServerJobSubmitter and select Connect Loggers.

This will add Logger transformers to the workspace so we will know the status of the completed jobs.

**6. Publish the Workspace**

Publish the workspace to FME Server, into the workflow_management repository and registered with the job_submitter service.

**7. Run Workspace**

Locate the workspace in its repository in the web interface. Select Job Submitter

Use the File Upload “Add Files” button to upload the files:

C:\FMEData2015\Resources\workflow_management\parcels_downtown.zip and

C:\FMEData2015\Resources\workflow_management\voting_downtown.zip files

For the two published parameters, first click
*From Recently Uploaded Files.*

Then, for the voting parameter, choose the newly uploaded dataset *voting_downtown.zip*

For the properties parameter choose *parcels_downtown.zip*

Click Run Workspace to run the workspace.

**8. View Log**

Once the workspace completes click the View Log button.
Scroll down the log until you see the logged feature.
If you see the Feature Type of the logged feature reported as FMEServerJobSubmitter_Succeeded_LOGGED then you know the child workspace was successfully triggered.

**9. Chain Workspaces – Part 1**

Now we can start to chain multiple workspaces together.

Go back to FME Workbench where the control workspace is open. Delete the Logger transformers and then add a second FMEServerJobSubmitter transformer. It should be connected to the Succeeded port of the first FMEServerJobSubmitter transformer.

Open the parameters dialog of the newly added FMEServerJobSubmitter and enter the usual connection details. This transformer will be used to execute the second workspace of the three, so select Exercise5c-Begin-Data-Process.fmw as the workspace to run.

Again, Set Wait for Server Job to Complete to Yes.

This is where it gets interesting. One of the attributes added to the features output from an FMEServerJobSubmitter transformer records the path to the dataset written by that workspace.

In other words, the first child process returned information about where it wrote its output data, and we can use that information to provide the input for the second child process.

In the Source SpatiaLite Database File(s) parameter, click the drop-down arrow. Select Attribute Value > output_datasets{}.path

Because this is a list attribute – i.e. there may be more than one value – you’ll be asked which value you want to use. It will be the first one; element 0

So select 0 (if it isn’t already) click OK to close this dialog, and Finish to close the main dialog.

**9. Chain Workspaces – Part 2**

Now add a third FMEServerJobSubmitter transformer – again connected to the Succeeded port of the previous – in order to run the third child workspace.

Again enter the connection properties and again choose the same repository as before. This time the workspace to select is Exercise5c-Begin-Data-Rasterize.fmw

Again, set Wait for Server Job to Complete to Yes and set the source SpatialLite Database to use the output_dataset{}.path parameter (element 0).

Finally, set the destination directory to be the Temp resources folder. To do this use $(FME_SHAREDRESOURCE_TEMP). Using a resources location allows the data to be accessed via the web interface and REST API.

Once more, click Finish to close the main transformer parameters dialog.

Then add some Logger transformers again, so we can keep track of the results.

**10. Publish Workspace**

Publish the workspace back to FME Server, again into the workflow_management repository and registered with the Job Submitter service.

In fact, since no service changes need to be made, you can simply use the Republish button.

**11. Run Workspace**

Run the workspace in the Web Interface, as in step 7. Remember to assign the uploaded data to the two published parameters.

**12. View Log**

Once the workspace completes, click the button View Log 

Again you should be able to find the same success message, indicating all three child workspaces have run to completion.

**13. View Data**

Once complete, click Resources on the sidebar menu and expand the Temp directory.

You will see the five PNG files that were created by this workflow.

You can now download these files and access them via the REST API.