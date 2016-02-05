# Layer Selection and Handling

Layer (Feature Type) flexibility can be achieved through the Feature Types to Read parameter.

There is no single method by which users might wish to select data or features. Every organization implementing FME Server lets users select data in different ways.

However, spatial data is often organized in layers (groups, classes, categories, feature types) and a common way that users will wish to choose data is on a layer-basis.

**Selecting Layers**

Allowing users to select data by layer is the simplest solution available in an FME Workspace, although in many situations users will wish to select data not just by layer, but by a mix of criteria.

Allowing choice by layer alone can be handled easily if the layers correspond to Feature Types in the source data.

Each reader in FME has a parameter called Feature Types to Read. When this parameter is published, the workspace will accept a list of layers to read from the user.

The publishing dialog for Feature Types to Read is different because FME can automatically scan the workspace and provide a list of available feature types.

Additionally, the Use Alternate Display Name allows the author to publish alternate names (for example Road Centrelines instead of RdCtrLns) in a similar way to the “Choice with Alias” parameter.

**Grouped Layers**

On some occasions the user does not need to be presented with a full list of layers. Instead they might need to see “groups” of layers.

For example, what is presented to the end-user as “Water” features may actually be made up of multiple source feature types such as Lakes, Rivers, and Streams.

This type of scenario can be achieved using a parameter of type “Choice with Alias (Multiple)”.

Here the author has eight feature types, but wishes to present them to the end-user as three groups of layers.

The first step is to create a parameter of type “Choice with Alias (Multiple)”:

In the parameter configuration, all feature types from the same group are given the same display name:

Finally, the Feature Types to Read parameter is linked to the newly created Choice with Alias parameter:

Now when the workspace is run, the end-user is presented with a set of three options (Environment, Buildings, and Amenities) that reflect a series of different layers/feature types.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3E </span>
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
<td style="border: 1px solid darkorange">The
Feature
Types
to
Read
parameter
for
layer
selection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3e-­‐Begin-­‐
DataDownload.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise3e-­‐Complete-­‐
DataDownload.fmw</td>
</tr>

</table>

The task here is to update the current data download service to deliver a hybrid image of aerial photo and map data. We’ll do this by adding a vector data Reader to the workspace and burning (stamping) it into the raster.

**1. Start Workbench**

Start FME Workbench (if necessary). Open the workspace from Exercise 3d (or the start workspace for this exercise).

Select Readers > Add Reader from the menubar and add a new Reader for some roads data with the following parameters:

Reader Format Bentley MicroStation Design (V8)

Reader Dataset C:\FMEData2015\Data\Transportation\RoadsDGN.dgn

Workflow Options Single Merged Feature Type

Click Parameters to open the parameters dialog.

In the dialog check Group Elements by Level Names and click OK. This will ensure data is added with the correct level names (not numbers).

Click OK again to add the Reader. You will see a single source feature type which will allow any layer to pass through.

**2. Merge Roads with Raster**

Vector data can be added into a raster image by using the VectorOnRasterOverlayer transformer.

Add a VectorOnRasterOverlayer to the canvas.

Connect the RasterMosaicker Output port to the VectorOnRasterOverlayer Raster input port and connect the new MicroStation Reader feature type to the Vector input port. Connect the Raster output port to the AirphotoMosaic.

**3. Modify the Feature Types to Read Parameter**

When you added the MicroStation Reader, a user parameter was automatically created to allow users to choose which level to read from the file.

In the Navigator pane browse to User Parameters > Published Parameters > FEATURE_TYPES; right-click the parameter and choose Edit Definition.

This opens a dialog that demonstrates the special nature of this parameter. However, as of yet there is no content filled in.

Check the parameter marked Fixed List. Then click the dropdown menu labelled List and choose Add from Current Dataset. Select all of the available feature types in the dataset and click OK.

This will basically create a list of layers for the end-user to select from.

**4. Set up Layer Groups**

As a final step in modifying this parameter, check the parameter labelled Use Alternate Display Name. This allows you to enter groups and aliases.

Edit the Display Names and give all the minor roads the name Secondary so that they become a group for the user.

Select Arterial as the default and click OK to close the dialog.

**5. Run Workspace in FME Workbench**

As always, confirm the parameters work as expected – and that the vector on raster overlay is working – by running the workspace using Run > Prompt and Run in FME Workbench.

When you check the Feature Types To Read parameter, you’ll notice that the options are Arterial (the default), Collector, and Secondary – the groups that you just created.

**6. Delete the MicroStation Source Dataset Parameter**

Your users do not need to know where the MicroStation file is coming from, nor do they need to see a parameter for it. By deleting the parameter, we’ll remove it from the user’s view and ensure it gets uploaded to FME Server.

In the Navigator pane, browse to User Parameters > Published Parameters > SourceDataset_DGNV8, right-click the parameter and choose the option to delete.

**7. Publish to FME Server**

Save the workspace as Exercise3e.fmw.
Select File > Publish to FME Server from the menubar to start the publishing process.

Fill in the connection details and credentials as usual and then click Next to continue.

In the next dialog select Training as the repository to publish to. However, do not yet click Next. Instead, click on the button labelled Select Files.

The Resources dialog shows what resources – such as source data – are being uploaded to FME Server along with the workspace.
Remember all GeoTIFF orthophotos are already uploaded, so uncheck those files from the list.

However, we do want to upload the MicroStation DGN file. In this case we’ll upload it to a repository (available only to this workspace) rather than to a Resources folder where it would be open to everyone.

Check to see where the file will be uploaded. If the dialog already says repository, then all is OK.
Else click the button to change the location and set it to repository.

When you click OK, a warning message will alert you to the fact that the GeoTIFF files are being referenced but not uploaded. That’s OK – we know the files already exist on the server – so simply click OK to dismiss the dialog.

Then click Next to pass on to the final dialog of the publishing wizard.

**8. Register with Data Download Service**

In the Register Services dialog check Data Download if it is not already.

Click the Edit button and confirm that the Output Dataset for the service is set to your Generic Writer.

Click OK to close the dialog and Publish to complete the wizard and publish the workspace.

**9. Run Workspace on FME Server**

In the Web User Interface run your workspace using the Data Download Service as if you are a user, as we have been doing in the previous exercises.

Notice how the Feature Types to Read parameter is a selection parameter, like this:

…letting the user select which roads layers (if any) they would like overlaid on the imagery.

Congratulations: Your Data Download service now lets the end-user retrieve data with a selection of required layers.