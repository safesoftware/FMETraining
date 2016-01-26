# Format Selection

Another obvious requirements in Self-Serve is to be able to select the format of data to be downloaded

One of the most useful parameters in a self-serve system controls the output data format. With a simple Generic format, FME allows the end-user to select this format on the fly, without any format-specific setup from the workspace author.

**The Generic Writer**

The Generic writer is a way to write data in FME where the output format is chosen at run-time.
This way a workspace may be created that can write to any format.

The output format is defined by a parameter so, by publishing the parameter, the user gets to choose the output format at run-time.

There are a couple of points to keep in mind when using the writer:

• The parameter for output format is automatically published, but in FME Server’s interface it appears only as a text field that accepts FME’s short form name for any format. Best practice decrees this should usually be replaced by a new Choice with Alias parameter; to reduce the list to a reasonable set of choices, with descriptive format names.

• Each writer format has its own specific parameters, and these may still need to be set when a generic writer is used. For example, a specific template file might need to be used when AutoCAD is chosen as the output format. This can be achieved by adding a writer of the same format and setting the parameters in that writer. The Generic writer will inherit the parameters of this dummy writer, even if no features are connected to it.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3D </span>
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
<td style="border: 1px solid darkorange">Improve
the
data
download
service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Providing
Coordinate
System
and
Format
Parameters
in
a
Data
Download
service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3d-­‐Begin -­‐
DataDownload.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3d-­‐Complete -­‐
DataDownload.fmw</td>
</tr>

</table>

The Data Download system from Exercise 3c is still lacking some important user options. Users have asked if they can set the destination coordinate system and data format in the Data Download service.

**1. Start Workbench**

Start FME Workbench (if necessary). Open the workspace from Exercise 3c (or the start workspace for this exercise).

**2. Delete JPEG Writer**

To allow selection of data format we’ll need to remove the existing JPEG format Writer and replace with a Generic Writer.

Locate and click on the JPEG Writer in the Navigator window. Press the delete key to remove it. You will receive a prompt confirming your actions. Click OK to accept the deletion.

**3. Add Generic Writer**

Now the JPEG Writer is removed, we can add a Generic Writer.
Select Writers > Add Writer on the menubar. When prompted enter the following settings:

Format Generic (Any Format)

Dataset C:\FMEData2015\Output\Training

Click the Parameters button to ensure these are set. If no output format is already set then select a format (it doesn’t matter what you choose) and click OK to close the dialog.

Under Add Feature Type(s), ensure Copy from Reader feature type definition is selected.

Click OK again to close the Add Writer dialog.

**4. Edit Feature Type**

When a new Writer is added with Copy from Reader selected, the writer inherits the schema of the specified reader feature type.

Click the cog wheel icon on the Writer feature type to open the properties dialog.

In this dialog uncheck the Dynamic Properties parameter and then type AirphotoMosaic for the Raster File Name.

**5. Connect Feature Type**

In the workspace, connect the new feature type to the RasterMosaicker Output port.

**6. Create a Format Parameter**

Now we’ve added a Generic format writer we should publish a parameter so that users can select the format to use. As in the previous example, right-click User Parameters in the Navigator window and select Add Parameter.

Use the following settings for your new parameter:

Type Choice with Alias

Name Format

Published Yes

Optional No

Prompt Choose Format

**7. Configure Parameter**

To configure the parameter click the ellipsis […] button next to the Configuration setting.

This will open a dialog in which to define the parameter configuration. Because this is a “Choice with Alias” parameter we need to define both values and a display name. However, since we are using this to select a format there is a nice shortcut that we can use to do so.

Click the Import drop-down and select Writer Format(s) from the menu. This provides a dialog with a list of Writer formats that we can add to our parameter.

Search for and add the following formats:

JPEG

ECW

GeoTiff

Then click OK to close this dialog and return to the configuration dialog. It should look like this:

Notice the Display Name column allows you to provide your users a description or alias for each entry. Edit these in any way you think makes them easiest to understand and click OK.

Choose any of formats as the default and click OK to create the parameter.

The following should now be the list of current published parameters:

**8. Link the Custom Format Parameter**

Now the format user parameter must be linked to the appropriate FME parameter.

In the Navigator window, locate the Generic Writer and expand its list of parameters. Locate the parameter Output Format and right-click upon it. Choose Link to User Parameter:

This will pop-up a list of user parameters. Select the newly created Format from the list.

**9. Create a Coordinate System Parameter**

Now we can create a parameter to control coordinate system.
Once again in the Navigator window locate User Parameters and right-click to Add Parameter.

Use the following settings for your new parameter:

Type Choice with Alias

Name CoordinateSystem

Prompt Choose Coordinate System

Published Yes

Optional No

**10. Configure Parameter**

To configure the parameter click the ellipsis […] button next to the Configuration setting.

This will open a dialog in which to define the parameter configuration. Because this is a “Choice with Alias” parameter we need to define both values and a display name. However, since we are using this to select a coordinate system there is again a nice shortcut that we can use to do so.

Click the Import drop-down and select Coordinate System(s) from the menu. This provides a dialog with a list of coordinate systems that we can add to our parameter.

Search for and add the following coordinate systems:

LL84

BCALB-83

UTM83-10

Then click OK to close this dialog and return to the configuration dialog. It should look like this:

Again, notice the Display Name column allows you to edit the display name to make it easier to recognize. Edit these in any way you think makes them easiest to understand, the click OK.

Choose any of coordinate systems as the default and click OK to create the parameter.

**11. Link Custom Parameter**

Now the coordinate system user parameter must be linked to the appropriate FME parameter.

In the Navigator window, locate the Generic Writer and expand its list of parameters. Locate the Coordinate System parameter and rightclick upon it. Choose Link to User Parameter:

Choose CordinateSystem from the list and click OK.

We now have user parameters set up for both coordinate system and format.

**12. Run Workspace on FME Desktop**

Save the workspace as Exercise3d.fmw.

Run the workspace using Run > Prompt and Run from the menubar.

The translation parameters dialog will open. Select a format and a coordinate system (and any existing parameters) and click OK to run the workspace.

Check the output folder (C:\FMEData2015\Output\Training) and inspect the datasets to ensure the translation is correct.

**13. Publish to FME Server**

Use File > Publish to FME Server to publish the workspace.
Publish it to the Training repository and register it with the Data Download service.

Notice that in the Register Services window the Data Download Service is highlighted red.

This occurs because we deleted the original JPEG writer to which data was being downloaded from.

We need to specify a Writer for the Service so click Edit and select “Training[Generic]” as the dataset to include for the Data Download Service.

Click Publish to finish publishing the workspace.

**14. Run Workspace on FME Server**

Changing once again to a user role, go to the Web User Interface and navigate to your workspace: Workspaces > Training > Exercise3d.fmw > Data Download

Notice your new parameters for format and coordinate system. Again select some image files from Browse Resources and this time choose one of the new formats and a coordinate system.

Run the workspace and then download your data to confirm the results.

Congratulations! Your self-serve Data Download service can now accommodate customers who work with different formats and coordinate systems.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“You might have noticed that we could just publish the Writer
dataset and coordinate system parameters directly, instead of
creating them manually and then linking the two.
This will work, but by using a Choice with Alias parameter we
can restrict the list of formats/coordinate systems, use an alias,
and also get them as a drop-down list in FME Server.
Otherwise they would be text-only parameters that would be
unlimited in what formats and coordinate systems were
available, as long as you could guess what value was required.”
</span>
</td>
</tr>
</table>