# The Generic Reader/Writer

The Generic Reader and Writer allow FME workspaces to be freed from format restrictions.

**Generic Formats**

FME’s generic tools are a Reader and Writer that are not tied to a particular format. The Generic Reader is capable of reading almost any format of data, and the Generic Writer is capable of writing almost any format of data.

In that way, a single workspace can be used to process different data formats without being specifically set up for that format.

**The Generic Reader**

Whereas all other Readers are tied to a particular format, the Generic Reader is capable of handling almost any format.

A Generic Reader is simply added the same way that any other Reader is used; by specifying the format in the new Reader dialog:

A parameter allows the format of the data being read to be specified, or it can be left up to FME to ascertain the format from the data extension of the source file.

Now at run time, the source dataset can be set to GML:

Or MapInfo TAB:

Or any other format of data you care to read (provided the data has the same schema). This makes for a very flexible workspace.

Generic Reader Feature Types

However, the Generic Reader is not immune from the Unexpected Input Remover. Remember, this is the functionality that filters incoming data against the list of feature types (layers) that are defined in the workspace. If the incoming data is stored on a layer that is not defined in the workspace, then it will be removed.

For this reason, you’ll want to ensure that all potential layers are defined as feature types in the workspace; or that you have a Merge Feature Type set in the Feature Type Properties dialog:

With that setup, any layer of data can be passed into the workspace:

**Generic Reader Parameters**

All Readers in a workspace have a number of parameters that can be used to control how that Reader operates. Each format has its own set of specialized parameters.

However, the Generic Reader has none of these.

So, for example, a user wishes to apply a particular parameter to a GML dataset read with the Generic Reader, how is it done?

In brief, the solution is to add a dummy GML Reader. In fact, a Resource Reader is the best solution, because it applies parameters without reading any data (more info on Resource Readers appears later in this chapter).

When the Generic Reader reads a dataset of GML format, it will now look to the parameters of the dummy Reader, and use those to set how it reads GML datasets.

For example, this workspace author uses a Generic Reader to read his GML data. It is a dataset of parks in the city but, sadly, the x/y axes are being read incorrectly:

There is a parameter to control the x/y axes in the GML Reader, but it doesn’t appear in the Generic Reader. So, the author selects Reader > Add Reader as Resource from the menubar:

When prompted the user defines the format as GML and picks a GML dataset (it won’t matter which).
In the Navigator window they locate the newly added Reader under Workspace Resources…

…and locates/set the GML Axis Order parameter:

Now when the workspace is run, the Generic Reader uses this GML resource to determine the parameters to read GML data with. The parameter is applied and the data read correctly:

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
“If the Input Format parameter is turned into a user parameter, then the
user can specify at runtime what format of data is being read. This is
especially helpful when the extension is – like .mdb – one used by
multiple formats.
Additionally, the workspace can be made to test for the format being read and then filter
the data to process different formats in different ways:”
</span>
</td>
</tr>
</table>

**The Generic Writer**

Similarly to the Generic Reader, the Generic Writer is a component of FME without a specific format.

A Generic Writer is simply added the same way that any other Writer is used; by specifying the format in the new Writer dialog:

When a workspace with a Generic Writer is run, the format of data written is determined by a parameter that can be set in the Navigator window:

This parameter is one of those that FME automatically creates a linked user parameter for.
That way the end-user can choose at runtime which format to write to.

The Destination Dataset parameter, like all dataset parameters, is also linked to a user parameter. Note that the destination for this writer is always a folder, even when the selected format is file-based.

For example, here the user is reading a parks dataset (coincidentally also using the Generic Reader) and writing the data out to KML format using the Generic Writer:

**Semantic Translations and the Generic Writer**

It’s important to remember that FME is a semantic translator, carrying out transformations on output data to fit the definitions and rules of the destination format.

In other words, FME will automatically restructure data to fit the output format’s rules on geometry and attributes (both names and values).

Therefore, the Generic Writer may produce slightly different results for different data formats.

**Generic Writer Feature Types**

The feature types defined for a Generic Writer are – like the Generic Reader – relatively inflexible. The layers that are defined will be the layers that are created, regardless of format.

Of course, there is a way to be more flexible – and creative – with the feature types that are written, and that’s with functionality that we just covered: Fanouts!

If the Generic Writer uses a feature type fanout, based on the format attribute fme_feature_ type, then the destination dataset will have the same layers as the source – even if that varies from translation to translation!

Generic Writer Parameters

Like the Generic Reader, a particular output format in the Generic Writer can be controlled using parameters from a dummy Writer of the same format, which has been added to the workspace.

The difference is that this will be a “real” Writer and not a Resource Writer (of which there is no such thing). The dummy Writer does not need to have any feature types defined, or any data sent to it; in fact it should not as this would only slow the translation.

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
“Generic Readers and Writers by nature only deal with a flexible format,
but can also be set up to be flexible with layers.
However, each dataset being read must have the same attribute schema, and each
dataset being written will end up with the same attribute schema. This part is not
flexible.
To work with flexible attribute schemas requires the use of either Automatic Attribute
Definitions or a Dynamic Translation.”
</span>
</td>
</tr>
</table>

In this exercise your task is to create a workspace with which end-users can output a dataset of Community Mapping in a format of their choice. This would be an excellent workspace to use for an FME Server Data Download service.

**1)** Start Workbench

Start FME Workbench and begin with an empty canvas. Select Readers > Add Reader from the menubar and add the following:

Reader Format: Esri Geodatabase (File Geodb API) Reader Dataset: C:\FMEData2015\Data\CommunityMapping\CommunityMap.gdb

Workflow Options: Single Merged Feature Type

By selecting the single merged feature type option we will have a workspace that is nice and compact, plus it will allow the user to select which tables they want to read from the source.

Click OK to close the dialog and add the Reader.

**2)** Add Writer

Select Writers > Add Writer from the menubar and add a Generic Writer.

You don’t have to select an output location, but will you have to open the parameters dialog and set an original output format; so do that and select a format like Esri Shape.

In the "Add Feature Types" section of the dialog, select Automatic for feature type definitions:

In the Feature Type Properties dialog set the Allowed Geometries field to fme_any. This will allow any data to be written to this feature type. The "output" part of the Writer refers to the output location, which may or may not be set in your workspace.

Check the User Attributes tab and you will see that the attribute definition is set to Automatic.

Click OK to close the dialog and add the new feature type. Connect it to the source feature type. When you make the connection the attribute schema will automatically be updated to match the connected Reader feature type:

**3)** Check User Parameters

Look in the Navigator window at the user parameters that were created automatically with the Reader and Writer.

The parameter for source dataset we don’t need (it will always be this dataset) so delete it.

Another parameter is Feature Types to Read. This is very useful because when the user runs the workspace they will be prompted which tables to read from the source Geodatabase, so keep this one.

Similarly keep the Destination Dataset parameter.

The Output Format parameter is interesting. Double-click on it as if you were going to set a value. Notice that the "More Formats..." option in the drop-down list opens up the full FME formats list.

It wouldn’t be fair to the end-user to expose so many formats, when they don’t really need to see or select most of them. It would be better to restrict this list. So, delete this user parameter, and we’ll create a new one.

**4)** Add User Parameter

Now add a new User Parameter, by right-clicking on User Parameters and selecting Add Parameter. In the dialog that opens…

Set type to Choice with Alias.

Set OutputFormat as the name.

Set Output Format as the prompt.

Turn off the Optional checkbox.

For configuration click the browse […] button to open a new dialog. In that dialog, select Import

- Writer Formats. Select a handful of the most common formats like Shape, AutoCAD DWG, GML, and MapInfo TAB; then click OK.

Then click OK twice more until all the dialogs are closed.

**5)** Link Parameter

Now, in the Navigator window, expand the parameters for the Generic Writer. Locate the Output Format parameter. Right-click it and choose Link to User Parameter.

Select the newly created OutputFormat parameter and click OK.
Now when the workspace is run, the choice of output format will be between these few:

**6)** Expose Format Attribute

The other, final, task we can do here is to output the features to their original table. To do this we need to know where they came from, and that is obtained from a format attribute called fme_feature_type.

Open the properties dialog for the Reader feature type and click the Format Attributes tab.

Put a checkmark next to fme_feature_type and click OK to close the dialog:

**7)** Set Feature Type Fanout

Now open the properties dialog for the Writer feature type. Check the box for Fanout by Attribute and select fme_feature_type as the attribute to fanout by.

**8)** Save and Run Workspace

Save the workspace and then run it using Prompt and Run. When prompted, select some source tables to read (include at least the GarbageSchedule plus one other) and set an output folder. Set Esri Shape as the format to write.

Examine the output folder. The selected tables have been written back to Shape format.

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
“Did you notice that FME handled the different geometry types and
output the files with the geometry as part of the name? It’s a Shape
format thing. FME can never – and will never – write more than one
geometry type to the same Shape file.”
</span>
</td>
</tr>
</table>

The one drawback is that each output Shape file has all of the attributes of the source data. To avoid that you would need to add each table in the source separately (as we can see in the Advanced Task below).

The one drawback is that each output Shape file has all of the attributes of the source data. To avoid that you would need to add each table in the source separately (as we can see in the Advanced Task below).

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">

</span>
</td>
</tr>
</table>

If the Writer feature type was set to a manual definition of the attribute schema, then we would be unable to use any other source data as the Generic Writer would be constrained by the fixed nature of this schema. However, since we made the attribute definitions automatic, it's now possible to run this workspace and use a different dataset... provided we add a new Reader too.

**9)** Add Reader

Select Readers > Add Reader from the menubar and add the following:

Reader Format: Esri Geodatabase (File Geodb API)
Reader Dataset: C:\FMEData2015\Data\Addresses\Addresses.gdb
Workflow Options: Individual Feature Types

There will be separate Reader feature types for addresses and postcode boundaries.

**10)** Connect Schema

In the workspace, disconnect the CommunityMap feature type from the Generic Writer, and instead connect the PostalAddress feature type. Notice that the schema will automatically update to match the Address data.

Run the workspace (setting a different output format such as GML)and inspect the output to prove that the Generic Writer is writing the format correctly, and that the automatic attributes setting is creating the correct attribute schema:

