# Schema Handling in Dynamic Translations

Dynamic Translations still use a schema, but it is not necessarily a carbon copy of the source dataset.

**Dynamic Translation Settings**

Opening the feature type properties dialog for a dynamic translation reveals the checkboxes that turns on this behavior.

For a Reader, all that is really happening is the merge feature type setting is turned on:

For a Writer, there is a special Dynamic option (it’s not just a feature type fanout):

So, it is possible to create a dynamic translation by turning one or both of these settings on manually; there’s no necessity to do so at the time the workspace is created.

The two extra parameters on the Writer are to control the source of the schema being used on the output dataset.

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
“Yes, a dynamic translation is often used to handle a variety of source
datasets, by automatically duplicating the incoming schema – feature
types, attributes, geometry types – on the output.
However, it’s also possible to dynamically select the outgoing schema from a completely
different location, or from an attribute in the data, or even by constructing a virtual
schema in the workspace!”
</span>
</td>
</tr>
</table>

**Schema Sources**

The schema sources parameter allows the user to choose where the destination schema is going to be obtained from.

By default, this parameter is set to whatever source dataset is being read. That way the output schema is always a duplicate of the input.

However, it can be set to use any Reader dataset – in any format – as the source for the outgoing schema. In the case where a Reader is only required to provide a schema, and not data, then it would be added as a Resource Reader.

For example, here the author has opened that parameter and is changing the output schema from the default (input dataset) to a standard corporate schema that is defined in PostGIS and has been added as a Resource Reader:

This is useful when you want to enforce a particular output schema, but it means that you have to ensure that the data being processed will match the feature types available in that schema.

If you write data to a dynamic Writer, and the feature types of that data do not match what is provided by the schema then it will be dropped:

Consider this behavior a sort of “Unexpected Output Remover”.

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
“In this scenario the “Dynamic” part of the translation is the destination
schema being fetched at run time.
For example, if the corporate schema (above) were to change, the workspace feature
types would not need updating. They would be automatically ‘updated’ when the
workspace is run.”
</span>
</td>
</tr>
</table>

**Schema Definition**

The Schema Definition parameter opens a dialog with a number of options:

These options are where a user can become very creative with their dynamic workspaces.

Remember, a schema is composed of three basic parts: Feature Types, Attributes, and Geometry Types. These settings give the author control over each part of that schema.

By default, each part is obtained from the incoming schema, whether that’s a real Reader or a Resource Reader. But these settings let the author pick alternative sources.

For example, the author could decide that the feature type name will be fixed (i.e. all output must match this set value), that the attribute definitions should come from feature types defined by an attribute value, and that geometry is set to a fixed type.

Here each incoming feature is assumed to possess an attribute called OutputLayer.

That attribute defines what feature type (layer) the data will be written to.

It also defines the Reader (or resource) feature type that the attribute schema will be taken from.

Finally, it specifies that the geometry of the output features must be area (polygon) features. Non-area features will be dropped.

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
Adding or Deleting Attributes
Even in a dynamic translation, sometimes you need to add or delete attributes from the output
schema. This is very simple to do.
</span>
</td>
</tr>
</table>

**Adding a New Attribute**

Adding a new attribute to all output on a dynamic feature type is just a case of editing the feature type definition to add that attribute.

In other words, any attribute you add to the feature type definition will get added to all features output through there – regardless of source or resource schemas.

For example, I might add an attribute if an AreaCalculator transformer was in the workspace and I wished to store the result.

**Deleting an Attribute**

Deleting an existing attribute is done through the dynamic Schema Definition dialog. At the foot of that dialog is a field for removing attributes:

The edit […] button opens a dialog in which to select attributes that are in the source schema but that you don’t want in the output. You can choose to select these existing attributes – or type in an entirely different value, if you know an attribute exists but is not exposed.

One of the datasets in the FMEData2015 folder is CommunityMap.gdb. This dataset is a series of base datasets used by the planning department for various community mapping tasks.
However, the planning department now wants to create a new community map dataset, with new data, but using the existing schema where possible. They also – for reasons that are unclear – want a format change to GML!
So, let’s create a new workspace to handle that scenario.

**1)** Inspect Data

At the moment two datasets have been identified as being required in the new community mapping Geodatabase. They are:

Format: GML (Geography Markup Language)
Dataset: C:\FMEData2015\Data\Emergency\FireHalls.gml

Format: MapInfo TAB (MITAB)
Dataset: C:\FMEData2015\Data\Parks\Parks.tab

So, inspect these two datasets in the FME Data Inspector, to become familiar with them. There was already parks data in the community mapping, but this time it is polygons, not points. The FireHalls data is entirely new for community mapping.

**2)** Start Workbench

Start FME Workbench and begin by generating a workspace as follows: Reader Format GML (Geography Markup Language)

Reader Dataset C:\FMEData2015\Data\Emergency\FireHalls.gml

Writer Format GML (Geography Markup Language)
Writer Dataset C:\FMEData2015\Output\NewCommunityMap.gml
Workflow Options Dynamic Schema

**3)** Add Reader

So far; so good. Now let’s add a Reader for the new parks data.

Select Readers > Add Reader from the menubar. Add a Reader as follows:

Format MapInfo TAB (MITAB)
Dataset C:\FMEData2015\Data\Parks\Parks.tab
Workflow Single Merged Feature Type

Connect the new Reader feature type up to the existing Writer feature type.

**4) **Add Resource Reader

One of the requirements was to use the existing schema where possible. With the firehalls it wasn’t possible, since that never existed in the CommunityMaps before.

However, the parks dataset does exist in the current CommunityMaps dataset, so we’ll need to use that schema.

So, select Readers > Add Reader as Resource.

When prompted, enter the following info:

Reader Format Esri Geodatabase (File Geodb API)
Reader Dataset C:\FMEData2015\Data\CommunityMapping\CommunityMap.gdb

Click OK and the Reader is added as a Resource:

**5)** Adjust Dynamic Parameters

Now we need to make sure that resource is being used.

Open the properties dialog for the Writer feature type. Under Dynamic Properties click the edit […] button for Schema Sources.

Put a checkmark against CommunityMap and ensure Parks is NOT checked. Click OK.

Now click the edit […] button next to Schema Definition.

Since we are writing both points and polygons, for some formats we might have to change the Geometry setting. But GML can cope with both geometry types and so this section is greyedout.

Click OK to close this dialog and OK again to close the Feature Type Properties dialog.

**6)** Save and Run Workspace

Save the workspace and then run it.

Inspect the output. There should be two layers: one for fire halls, the other for parks. The parks dataset should have a schema of ParkName, ParkAddress, and ParkURL (even if there is no data to fill some fields yet). However, notice that it also has OBJECTID, which came from the Geodatabase and we don’t really need.

**7)** Delete Attribute

Re-open the properties dialog for the Writer feature type. Under Dynamic Properties click the edit […] button next to Schema Definition.

Click the […] button at the foot of the dialog next to Attributes to Remove.

In the dialog that opens, type OBJECTID into the first field. You won’t be able to select it from the drop-down list because it comes from a resource reader, not a real reader.

Click OK to close that dialog, then once more to close the Schema Definition dialog.

But don’t close the Feature Type Properties dialog yet.

**8)** Add Attribute

A last-minute request is to add an attribute – LastUpdatedBy – to all tables in the output.

So, click on the User Attributes tab and add this new attribute. Make it a 30 character string.

**9) **Re-Run Workspace

Save the workspace and run it again.

Inspect the output. Notice that OBJECTID will not appear as an attribute. LastUpdatedBy does appear, albeit that it doesn’t have a value yet.