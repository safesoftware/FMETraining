# Fanouts

Fanouts are one of the most powerful pieces of functionality within FME, capable of producing impressive results with very little effort.

**What is a Fanout?**

Fanouts are a way for the workspace author to divide data up into groups of features, as the final step of a translation.

Because a fanout occurs as the data is being written, it does not cause multiple flows of data inside the workspace. Therefore this technique makes it easy to create groups with minimal impact on the workspace canvas.

Similarly to a group-by, the groups are defined by an attribute.

For example, here an author is “fanning-out” a set of data into multiple outputs depending on a feature’s elevation attribute:

A major benefit of a fanout is the high degree of flexibility – and freedom from fixed-layer schemas – in return for minimal effort.
There are two types of fanout: Feature Type Fanout and Dataset Fanout.

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
“If this technique sounds familiar, that may be because it carries out a
similar function – albeit in reverse – to the “Merge Feature Type”
parameter.”
</span>
</td>
</tr>
</table>

**Feature Type Fanout**

A Feature Type Fanout delivers data to multiple feature types (layers) within a single dataset.

Taking the elevation example, here the output is a different feature type for each elevation value:

This results in a DXF dataset containing multiple layers of data.

A feature type parameter is defined using an option in the Feature Type Properties dialog:

**Dataset Fanout**

A Dataset Fanout delivers data to the same feature type, but in multiple datasets.

Taking the elevation example again, here the output is a different dataset for each elevation value.

This results in a series of DXF datasets, each of which has one elevation’s worth of contours on one layer.

A Dataset Fanout is defined in the Navigator window in Workbench, under a Writer’s Advanced Parameters.

Like a Feature Type Fanout, there is a parameter to select the attribute to fanout on. However, there are also parameters to let the author define a prefix and suffix for the fanned-out file names.

You’ve been given a dataset of development zones and asked to separate each zone type into a separate Shape file and send it back with everything zipped together in a single file.

The requestor thinks this will be a difficult task; but with FME you should be able to do it in about two minutes.

**1)** Inspect Source Data

The source data for this translation is a MapInfo TAB dataset:
C:\FMEData2015\Data\Zoning\Zones.tab

Inspect the source dataset in the Data Inspector. Notice that there is a field called ZoneName.
We need the first characters of this field (up to any “–“ character) for our fanout.

**2)** Start Workbench

Start Workbench and generate a workspace to translate the MapInfo source data to Esri Shape.

By default the workspace will include a GeometryFilter and multiple output feature types.
However, we know the data is polygon only (because we inspected it first, right?) so we can remove much of this.

So, delete the GeometryFilter transformer and all of the Writer feature types except Zones_ polygon. You’ll end up with something that looks like this:

**3)** Add StringReplacer Transformer

To remove everything after the “-“ character in the ZoneName field, place a StringReplacer transformer into the workspace, between the Reader and Writer feature types.

**4)** Set Parameters

Open the parameters dialog for the StringReplacer.

For the Attributes field, select ZoneName.

For the Text to Match enter: -(.+)$

Leave the Replacement Text field empty.

Select Use Regular Expressions = Yes (this is very important)

This regular expression will search out the dash character – and anything after it – and replace it with nothing (i.e. delete it). Click OK to close the dialog.

**5)** Set Fanout

Open the Feature Type Properties dialog for the Writer feature type. Set the Fanout by Attribute checkbox on and select ZoneName as the attribute to fan out by:

Click OK to close the dialog.

**6) **Save and Run Workspace

Save the workspace. Run the workspace using File > Prompt and Run.

When prompted manually change the Destination Directory to:
C:\FMEData2015\Output\Zones.zip.

Open the output folder in a file browser.

You should see the file Zones.zip. If you open it up there will be inside a Shape file for every zone type.

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
“A feature type fanout results in multiple Shape files because each
Shape file is a layer (feature type).
Why not repeat the exercise to get DWG files, in which case you’d need to use a Dataset
Fanout.”
</span>
</td>
</tr>
</table>