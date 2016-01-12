# Dynamic Translations

Dynamic Translations are a way to create ‘schema-less’ workspaces.

**What are Dynamic Translations?**

In previous chapters all translations have involved a schema being defined within the workspace. In other words, the source and destination schema reflect the structure of the source data (what we have) and the destination data the user requires (what we want).

The layout of a dynamic translation does not reflect either the source or destination schema. It’s a universal layout that is designed to handle data regardless of what schema is being used.

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
“For this section it’s useful to think of a schema being comprised of a
trinity of objects: feature types, attributes, and geometry type.”
</span>
</td>
</tr>
</table>

On the Reader side of things, a dynamic workspace is very similar to using Merge Parameters; feature types are given free entry to a workspace, regardless of whether they are yet defined in there.
Data is also read regardless of attributes and/or geometry type.

The Writer side of a dynamic workspace mimics the Reader part; feature types are written to the destination dataset, regardless of whether they have been defined in the workspace.

Additionally, all attributes and geometries are also written, regardless of whether they too have been predefined in a Writer feature type.

**Creating a Dynamic Translation**

When an author creates a translation using the Generate Workspace dialog, there are two options for what is called workflow: static schema and dynamic schema.

The Static Schema option is the default for a workspace including schema. Choosing the Dynamic Schema option creates a schema-less workspace with dynamic Readers and Writers.

The Add Writer dialog also has options for Static and Dynamic schema; so too does the Add Reader dialog, although there they are described a little differently.

In this way it’s possible to define individual readers and writers as ‘dynamic’.

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
“You can use any Reader and Writer format in conjunction with a
dynamic workflow; so don’t get confused with the Generic Reader and
Writer formats.
The term “Generic” means “any format”, while “Dynamic” means “any schema”. A
workspace may be generic, or dynamic – or both!”
</span>
</td>
</tr>
</table>

**How Does a Dynamic Translation Look?**

Both dynamic readers and dynamic writers each have a single Feature Type, regardless of the schema of the Reader datasets.

Notice that there is only a single feature type, regardless of whether the data is made up of several layers.

Also notice that the sole Reader Feature Type is named ‘<All>’ (which provides a clue to what is happening here) and that the sole Writer Feature Type is named ‘DYNAMIC’.

When the workspace is run, all of the source data is read through a single feature type. On the Writer side, although there is only one output type, the data will be dynamically divided back into its component layers, keeping its original attributes and geometry type.

In the previous exercise, a workspace was generated to translate a Geodatabase dataset into a number of formats using the Generic Writer.

However, now you feel it would be useful if that workspace could handle any source Geodatabase, not just the community maps dataset, without having to add new Readers or feature types every time.

So, let’s create a new workspace to handle that scenario.

**1)** Start Workbench

Start FME Workbench and begin by generating a workspace as follows:

Reader Format Esri Geodatabase (File Geodb API)
Reader Dataset C:\FMEData2015\Data\CommunityMapping\CommunityMap.gdb

Writer Format Generic
Writer Dataset C:\FMEData2015\Output\Training
Parameters
Output Format Esri Shape
Workflow Options Dynamic Schema

**2)** Inspect Workspace

Inspect the newly created workspace.

There is one Reader feature type and one Writer feature type. The Reader feature type shows a list of attributes, but the Writer feature type doesn’t. It is, however, labelled Dynamic.

Again, there will be a user parameter for the Feature Types to Read and the output format.

If you wish, create a more-limited version of the output format parameter, by following steps 3-5 in the previous exercise; although this isn’t totally necessary for what we’re doing here.

But don’t delete the Source Dataset user parameter; we’ll need that shortly.

**3)** Run Workspace

Run the workspace using Prompt and Run.

When prompted, select some source tables and set the output format.
The workspace will run to completion. Check the output to ensure it is all correct.

**4)** Re-Run Workspace

Now run the workspace again.
This time click the browse button for the source Geodatabase and browse to C:\FMEData2015\Data\Addresses\Addresses.gdb

Choose the feature types to read and this time you will be presented with a list of feature types from the newly selected Geodatabase.

Click OK to run the workspace again. Inspect the output. Notice that the output feature types are all as listed in the original data. Also notice that the attributes are as in the original too!

From this we can see that a dynamic workspace is capable of handling any source schema and writing it out to a new dataset just as it was in the source data.