# Workspace Design #

A basic workspace in FME is constructed and laid out strictly to the concept of ETL: Extract-Transform-Load

However, there are multiple other methods for constructing more advanced workspaces, and for directing the flow of data through a workspace in unique ways. 

![](./Images/Img3.000.WorkspaceDesign.png)

Some example uses for these techniques might be:

- To design large-scale workspaces a small section at a time
- To read data from multiple formats within a single workspace
- To carry out actions *after* a dataset has been written
- To use data stored on web services
- To test run individual parts of a workspace



# Prototyping #

In the classical sense, prototyping means creating an incomplete application as a way to evaluate the feasibility of a project.

Here we'll stretch the definition to mean how to build a complex FME project incrementally; starting with an empty workspace and building it piece by piece to deliver a result that matches the final specification.

This includes what techniques are useful for building a workspace incrementally, and how to handle data that is rejected by a transformer.

## Incremental Development ##

The key development technique for FME workspaces is [incremental updates](https://en.wikipedia.org/wiki/Incremental_build_model). 

The steps to this technique are:

- Plan your project as a series of small sections, each of which would fit inside a bookmark in FME
- Design and implement a section in FME Workbench. It should ideally be between 3-10 transformers.
- Test each section immediately after it is completed. That way you can identify problems at an early stage, and identify them more easily because only a few changes are being made in any increment.
- Repeat the process, saving the workspace and testing it whenever you've added a new section

Although a range of 3-10 transformers is an arbitrary number, the more transformers you add the more difficult it would be to identify the source of any problems. Beyond ten transformers is the point at which you should consider chopping that process into smaller sections.

Here an author has planned their workspace by laying it out as a set of bookmarks in the canvas:

![](./Images/Img3.002.TranslationPreDef.png)

Now the author can complete and test each section at a time, keeping the overall goal in mind at the same time.

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
It can be all too easy to start developing a workspace and forget to save it at all! FME keeps a recover file as soon as the workspace is saved for the first time, but until then you are running the risk of an irretrievable loss.  
</span>
</td>
</tr>
</table>

---

### Source Data ###

When the FME project is large and complex, it's likely that the source data will be large and complex too. So when creating a workspace in small increments, testing each part in turn, it's better to avoid using the entire dataset.

It's better to use a sample of source data for testing. In fact, it's better to actually create a small sample of data - extracting it from your source and writing to a neutral format like FFS - rather than randomly sampling the data for each test run.

This is particularly true for databases, because it also avoids the problems of waiting for network traffic and database responses.

![](./Images/Img3.003.SourceDataSample.png)

Here the workspace author is extracting a section of source data by reading from a database, splitting it into tiles, and writing just one tile to the FFS format. This one tile can be used for prototyping a solution in a way that is representative of the entire source database table. 

Another transformer to use would be the Sampler, although the features selected by it would not be spatially adjacent.

---

### Version Control ###

When making a set of incremental changes to a workspace, it's easy to mistakenly work on a single workspace file only. There are various problems with this:

- Faults cannot be easily tracked because there is no record of what has changed and when
- It is not easy to create different versions for different platforms
- If the workspace file is lost or corrupted then the entire project is lost

Therefore, it is better to keep versioned workspaces, where a different copy is kept for each set of revisions. This can be done manually within the file system, or by using a repository tool like Git. 

In fact, it is a good idea to keep and version all materials related to an FME project, including:

- Workspace files
- Python files
- Log Files
- Source Datasets

It's better to not store any information that is personal or that includes passwords. Also there's no need to store temporary files.

---

<!--Tip Section--> 

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
FME Server has a version control system built in. Even if you don't have an FME Server license, you can still install it for use as a repository system for workspaces and related files.
</span>
</td>
</tr>
</table>

## Rejected Features ##

An important part of any workflow is handling data that fails processing; for example where a feature with no geometry is sent into a geometry based transformer like the AreaBuilder.

FME handles such failures by outputting the data through &lt;Rejected&gt; ports, which are found on many transformers: 

![](./Images/Img3.004.RejectedPorts.png)

To give the workspace author a choice over what action to take, a parameter exists to control the action of &lt;Rejected&gt; ports.


### Rejected Feature Handling ###

The parameter to control handling of rejected features can be found in the Navigator window, under Workspace Parameters:

![](./Images/Img3.005.RejectedFeatureParameter.png)

The two options are *Terminate Translation* and *Continue Translation*.

When the parameter is set to terminate, then a feature that exits via a &lt;Rejected&gt; port causes the translation to stop. To visually denote this, the &lt;Rejected&gt; ports have a red marker on them.

When the parameter is set to continue, then the translation will continue, regardless of how many features exit &lt;Rejected&gt; ports. In that case the red marker is removed:

![](./Images/Img3.006.RejectedFeatureMarkers.png)

In terminate mode, a rejected feature gets written to the log window with the error message:

<font color="red">

    The below feature caused the translation to be terminated

</font>

There will also be an error message relating to the transformer:

<font color="red">

    AreaBuilder_<Rejected>(TeeFactory): AreaBuilder_<Rejected>: 
	Termination Message: 'AreaBuilder output a <Rejected> feature.

</font>

This error is useful because it tells the author which transformer experienced the failure.


### Mixed Mode ###

In terminate mode, a rejected feature will not cause the translation to terminate, provided that the &lt;Rejected&gt; port is connected to a further object:

![](./Images/Img3.007.RejectedFeatureMixedMode.png)

In short, an author can create a mixed mode, where some transformers terminate on rejecting a feature (the AreaBuilder above), but others will handle the feature another way (the AttributeRounder). That way the author can try to handle rejected features that are expected, but stop the translation if there are truly unexpected failures.

### Feature Counts and Inspection ###

In continue mode, features that exit a &lt;Rejected&gt; port are counted and saved for inspection:  

![](./Images/Img3.008.RejectedFeatureCount.png)

This occurs even if there is no Logger or other transformer attached. The number tells us how many features were rejected and the green icon can be clicked to inspect the data.

# Reading and Writing Workflows #

By default, the Generate Workspace dialog creates workspace with a single reader and a single writer. However, this does not mean the workspace is forever limited to this. Additionally FME can read/write data using:

- Multiple readers and/or writers
- FeatureReader and/or FeatureWriter transformers
- Integration transformers such as the DropboxConnector, Email, HTTPCaller, etc




## Workspace Components ##

A workspace is the primary element in an FME translation and is responsible for storing a translation definition. Think of a workspace as the container for all the functionality of a translation, which are stored in the following components:


### Readers and Writers ###
A **reader** is the FME term for the component in a translation that reads a source dataset. Likewise, a **writer** is the component that writes to a destination dataset. 

Readers and writers are represented by entries in the Navigator window.


### Feature Types ###
**Feature type** is the FME term that describes a subset of records. Common alternatives for this term are *layer*, *table*, *sheet*, *feature class*, and *object class*. For example, each layer in a DWG file, or each table in an Oracle database, is defined by a feature type in FME. 

Feature types are represented by objects that appear on the Workbench canvas.


### Features ###
**Features** are the smallest single components of an FME translation.

They aren’t individually represented within a workspace, except by the feature counts on a completed translation.

### Relationships ###

Each workspace can contain multiple readers and writers, each of which can have multiple feature types, with multiple features. They exist in a hierarchy that looks like this:

![](./Images/Img3.001.TranslationComponentsSmall.png)

## Multiple Readers and Writers ##

An FME workspace is not limited to any particular number of readers or writers; readers and writers can be added to a workspace at any time, any number of formats can be used, and there does not need to be an equal number of readers and writers.

For example, the Navigator window shows this workspace contains three readers and two writers, of different data types and formats!

![](./Images/Img3.009.MultiReadersWriters.png)

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
It's important to note that readers and writers don’t appear as objects on the Workbench canvas. Their feature types (layers) do, but readers and writers don't.
<br><br>Instead they are represented by entries in the Navigator window, as in the above screenshot.
</span>
</td>
</tr>
</table>

---

### Adding Readers and Writers ###

Additional readers or writers are added to a translation using the Quick Add menu:

![](./Images/Img3.010.QuickAddReader.png)

...Or by selecting Readers &gt; Add Reader (Writers &gt; Add Writer) from the menubar:

![](./Images/Img3.011.MenuReader.png)

This action opens a dialog, similar to the Generate Workspace dialog, in which the parameters for the new reader or writer can be defined:

![](./Images/Img3.012.ReaderWriterDialog.png)

As many readers and writers as required can be added in this way.

---

<!--Tip Section--> 

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
A reader can also be added by dragging a dataset from a filesystem explorer and dropping it onto the Workbench canvas.
</span>
</td>
</tr>
</table>

---

### Removing a Reader or Writer ###

If a reader or writer is no longer required, then it can be removed very simply using options on the menubar:

![](./Images/Img3.013.MenuReaderRemove.png)

Alternatively it's possible to right click a reader/writer in the Navigator window and choose the Delete option.

---

### Updating a Reader or Writer ###

Readers and writers can be updated so that older workspaces have the speed and functionality available in a newer version of FME. This is done by right-clicking the reader/writer in the Navigator window and choosing the Update option:

![](./Images/Img3.014.ReaderWriterUpdate.png)

For readers this tool provides the option to either just update the reader, or to also update the list of feature types being read. This way the workspace can be updated if the source data changes. Another way to update feature types is Reader &gt; Update Feature Types on the menubar.

## FeatureReader and FeatureWriter ##

Besides being able to read data with a reader and writer, FME has transformers specifically designed to read and write data. These are the FeatureReader and FeatureWriter transformers.

![](./Images/Img3.015.FeatureReaderWriterCanvas.png)

The advantage to these transformers is that they have an input port (FeatureReader) and output ports (FeatureWriter). So where a reader is always the first action in a workspace, and a writer is always the last, a FeatureReader and FeatureWriter can read and write data at any point in a translation.

---

### FeatureReader ###

The FeatureReader is set up with parameters to read a specific dataset:

![](./Images/Img3.016.FeatureReaderParameters.png)

Any feature that enters the Initiator input port will cause the data to be read, like here where a Creator supplies a null feature to trigger reading:

![](./Images/Img3.017.FeatureReaderCreatorInput.png)

The Creator creates a single feature that triggers the FeatureReader to read a dataset of park features. If, for some reason, the Creator created ten features, then the data would be read ten times, resulting in 800 output features!

#### Dataset from an Attribute ####

A common case with the FeatureReader is to supply the dataset to read as an attribute:

![](./Images/Img3.018.FeatureReaderExcelInput.png)

This example includes both reader and FeatureReader. The workspace reads an Excel spreadsheet containing a list of public artworks. Each artwork has an attribute that points to a JPEG file containing a photograph of the artwork. 

The FeatureReader is set up to use the attribute as the filename to read. The result is that 18 rows are read from the Excel spreadsheet, and the equivalent 18 JPEG images exit the FeatureReader.

#### Spatial Filters ####

A key parameter in the FeatureReader sets a spatial filter on the data being read:

![](./Images/Img3.019.FeatureReaderSpatialFilter.png)

The Initiator Contains Result filter (for example) means that features output the FeatureReader if their geometry falls inside the geometry of the initiator feature. For example here:

![](./Images/Img3.020.FeatureReaderSpatiallyFiltered.png)

A dataset of parks supplies input features that trigger reading from a database address table. A spatial filter is applied so that the only addresses to emerge are ones that fall inside a park.

---

### FeatureWriter ###

The FeatureWriter is set up with parameters to write a specific dataset:

![](./Images/Img3.021.FeatureWriterParameters.png)

The dialog allows definition of the format and dataset to write, plus the feature types that are to be written and their attributes. In short, all of the parameters, settings, and schema definition required for a writer, appear in this single dialog.

Feature types can be manually defined within the dialog itself, or can be added automatically by connecting to the *Connect Input* input port:

![](./Images/Img3.022.FeatureWriterCanvas.png)

Notice also that an important part of the FeatureWriter is that its exit ports can be connected to other transformers for further processing. In the above screenshot the data is sampled to provide a single feature, then messages are sent via Twitter and email. 


## Read/Write with Integration Transformers ##

Readers and FeatureReaders can both read data locally, with a database, or using a web service:

![](./Images/Img3.023.ReaderWebSource.png)

However, sometimes it's useful to be able to use a transformer to read (or write) to a web or other integrated service. There are various reasons, but a key one is to be able to read a file itself, rather than reading features from it; for example being able to extract a JPEG file from Dropbox and store it as an attribute (rather than reading it as an actual raster feature).


### Integration Transformers ###

There are multiple transformers in the Integrations category of the Transformer Gallery:

![](./Images/Img3.024.IntegrationsTransformers.png)

Not all of them are for reading, writing, or copying files; some of the ones that are, are:

<table style="width: 100%;">
<tr>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> AutodeskA360Connector</td>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> BoxConnector</td>
</tr>
<tr>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> DropboxConnector</td>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> FMEServerResourceConnector</td>
</tr>
<tr>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> GoogleDriveConnector</td>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> OneDriveConnector</td>
</tr>
<tr>
    <td style="border: 1px solid white; background-color:white; padding:2"><strong>&bull;</strong> S3Connector</td>
</tr>
</table>

In this example the author is reading a dataset of parks and passing the features to a DropboxConnector:

![](./Images/Img3.025.DropboxImageRead.png)

Each park feature has the name of a JPEG image that is stored in Dropbox. The DropboxConnector transformer is set up to read that image and store it as an attribute (ParkImage) on the feature.

The features are then sent to a PostGIS database - using a FeatureWriter transformer - where the ParkImage attribute is written to a binary (bytea) column.

---

<!--Tip Section--> 

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
Instead of fetching files from Dropbox, the DropboxConnector - as with most Connector transformers - is also capable of uploading content as a file.
</span>
</td>
</tr>
</table>

# Workspace Testing Techniques #

When developing a workspace incrementally, or making edits to a structured workspace, a lot of testing will take place. Each time a change is made the author will wish to test the change, and this process of change/test repeats itself again and again.

To effectively and efficiently carry out this process, there are a number of tools available in FME Workbench.

The first set of tools are for inspecting data as it changes. The second set of tools are for defining which parts of the workspace need to be tested.

## Integrated Inspection ##

When developing and testing a workspace it's necessary to inspect the data being produced on a regular basis. To do this there are various methods to send data directly to a data inspection window.

### Redirect to Inspector ###

The simplest method to see output before it is written is to use the Redirect to FME Data Inspector option:

![](./Images/Img3.026.RedirectOutput.png)

In this scenario all data is sent to the Data Inspector instead of being written; so no output is produced and the data can be checked for flaws before writing.

### Inspector Transformers ###

In most cases it's necessary to inspect data at certain points in a workspace - not at the very end - and this can be done with Inspector transformers:

![](./Images/Img3.027.InspectorTransformers.png)

For example here the author has attached Inspectors to three different transformers.


### Feature Caching ###

Sometimes it's important to be able to inspect data at any step of the translation. Adding an Inspector transformer at every step would be tiresome, so instead FME has an option to cache data automatically.

This behaviour is activated using Run &gt; Run with Feature Caching on the menubar:

![](./Images/Img3.028.RunWithCaching.png) 

With this option active, FME generates caches at every step of the translation when the workspace is run:

![](./Images/Img3.029.GreenCaches.png)

The caches are indicated by the small icons on each object. In the above screenshot the caches are green, but they can change to yellow or red depending on how fresh the data is.

---

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Run with Data Caching is essentially the same as Run with Full Inspection in prior versions of FME. It has been renamed in FME2018 to better match new functionality that takes advantage of these caches.
</span>
</td>
</tr>
</table>

---

### Inspecting Cached Data ###

Cached data can be inspected by simply clicking on the icon on a particular object.

![](./Images/Img3.030.InspectACache.png)

---

<!--Tip Section--> 

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
It's certainly quicker to set up "Run with Data Caching" than to manually add Inspector transformers. However, be aware that caching data obviously causes the translation to be slower, and to use system resources such as disk space. 
<br><br>Data caching is very useful while developing a workspace, but should be turned off before putting a workspace into production.
</span>
</td>
</tr>
</table>


## Partial Runs ##

A partial run is when only one section of a workspace is executed. One way to do this is to disable objects in the canvas to only run certain enabled sections. Another method is to use a tool called Partial Runs, which is represented by pop-up options when a workspace is run with caching turned on.

The technique you use will depend on how large the workspace is, and how much of it you need to run. You may use one technique or the other - or you may use both!

---

### Disabled Objects ###

If designed correctly, a large workspace should be made up of small sections. Isolating a section (or part of a section) for testing is possible by disabling connections to all other components.

Here an author has disabled a single connection:

![](./Images/Img3.031.DisabledConnection.png)

Therefore the bottom part of that section will operate as normal, and can be tested without having to also run the top half. 

A connection is disabled by right-clicking it and choosing the option to Disable (or selecting it and using the shortcut Ctrl+E):

![](./Images/Img3.032.DisablingConnection.png)

A disabled connection is rendered inoperative in much the same way as if it had been deleted, and no features will pass through. The same disabling can be done to other canvas objects such as transformers and feature types. Even a reader/writer can be disabled through the Navigator window.

---

### Partial Runs ###

When caching is turned on, running a translation causes data to be cached at every part of the workspace. In subsequent runs, those caches can be used instead of having to re-run entire sections of workspace.

Here, for example, a workspace has been run with caching turned on:

![](./Images/Img3.033.CachedForPartialRun.png)

Now the author makes a change to the AreaCalculator parameters:

![](./Images/Img3.034.StaleCacheFromEdit.png)

Notice that the caches change color (to yellow) on the AreaCalculator and subsequent transformers. This denotes that caches are stale; their data contents no longer match what the workspace would produce.

To get the new results the author must re-run the workspace. However, they do not have to re-run the entire workspace; they can simply start the workspace at the point of change - the AreaCalculator:

![](./Images/Img3.035.CacheRunFromHere.png)

*Run From This* causes the workspace to run from that point only, using data cached up until that point. Notice how hovering over the option causes all "downstream" transformers to be highlight. They are the only ones that will be run. That makes the translation quicker.

The other option is *Run To This*. The author could use that option on the writer feature type and get much the same effect:

![](./Images/Img3.036.CacheRunToThis.png)

...but notice how the second branch from the StatisticsCalculator does not get highlighted. It will not be run. That shows how you can avoid running a particular section of workspace, in much the same way as if that connection had been disabled.

---

<!--Tip Section--> 

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
A partial run is particularly useful in avoiding re-reading data from its source; especially when the data comes from a slow, remote location such as a web service.
<br><br>Also, caches can be saved with the workspace, when it is saved as a template. That means the workspace can be re-run using the caches from a previous session or even from another author!
</span>
</td>
</tr>
</table>

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Partial runs are not compatible with variables (VariableSetter/Retriever transformers).
</span>
</td>
</tr>
</table>

# Module Review #
This session was designed to help you understand how a translation is put together, the best ways of creating it, how to read data in different ways, and how to test different sections of a workspace.

 
## What You Should Have Learned from this Module ##
The following are key points to be learned from this session:

### Theory ###

- A workspace is made up of a readers, writers, and feature types. They exist in a hierarchical structure.
- Incremental development is a way of constructing a workspace, one section at a time.
- A workspace can consist of any number of readers and writers - or none at all
- FeatureReader and FeatureWriter transformers read and write data at any point in a workspace
- Integrated inspection is a set of functionality to inspect data from within FME Workbench
- Partial runs allow specified sections of a workspace to run in isolation

### FME Skills ###

- The ability to create a workspace one section at a time
- The ability to handle rejected data in a workspace
- The ability to add new readers and writers to a workspace
- The ability to use FeatureReader and FeatureWriter transformers
- The ability to read data from and write data to, web services
- The ability to inspect data using functionality in FME Workbench
- The ability to run selected sections of a workspace 


# Questions #

Here are the answers to the questions in this chapter. 

---




# Workspace Design #

- Creating a workspace incrementally.
- Add reader/writer
- FeatureReader/Writer
- Partial runs
- 


<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Residential Garbage Collection Zones</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase), Zones (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create boundaries for residential garbage collection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Workspace prototyping</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex1-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex1-Complete.fmw</td>
</tr>

</table>

The city maintenance department has a dataset of garbage collection schedules, to assign residents to collection on a particular day:

![](./Images/Img3.200.Ex1.ExistingZones.png)

However, because of shifting demographics and zoning changes, they have decided that new boundaries should be drawn. 

Your task is to use FME to create new boundaries. You must create five polygons, adjacent to each other, and with approximately the same number of residents in each. The analysis will be based on the city's address database. An estimate of the number of residents per address will be created depending on the zone type it falls within:

- Single-family residences: 2 adults
- Two-family residences: 4 adults
- Multi-family residences: 12 adults
- Comprehensive development zone: 8 adults
- Commercial properties: 1 adult

The output format shall be OGC GeoPackage.

To develop this workspace it's necessary to consider what different steps might be required. We can then create sections with a bookmark and fill them in as we go along.


---

<!--Tip Section--> 

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
If you wish to use a predefined workspace with this information, then open the starting workspace listed above and go ahead to step 2. To plan out the different sections of workspace, continue to step 1.</span>
</td>
</tr>
</table>

---

<br>**1) Plan Workspace**
<br>Let's plan this workspace together.

First of all we need to read the address data (or a sample of it) and write the output to Shapefile.

We need to know which zone type each address falls inside; to do this needs zoning data to be read and a transformer to carry out a spatial join.

We need to create a resident count based on the zone type and then we need to divide the residents into five different areas.

Finally we need to group the addresses together and create a boundary shape around them. In short, we need this set of actions:

- Read/Sample Address database
- Read Zoning data
- Create a spatial join
- Calculate resident count
- Divide residents into five groups
- Aggregate the addresses into their group
- Create a boundary shape
- Write Shapefile

So, firstly generate a workspace to translate the following: 

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Esri Geodatabase (File Geodb Open API)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Addresses\Addresses.gdb (PostalAddress table only)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">OGC GeoPackage</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training\GarbageZones.gpkg</td>
</tr>

</table>

Once the workspace is generated, add bookmarks to it to represent the different steps required. As yet we can't be sure which sections will be larger, so they can all be the same size.


<br>**2) Original Workspace**
<br>You should now have a workspace that looks like this:

![](./Images/Img3.201.Ex1.StartingWorkspace.png)

If you used the predefined workspace, you'll also find a bookmark containing all of the transformers required for the exercise:

![](./Images/Img3.202.Ex1.RequiredTransformers.png)

Or at least, these are the transformers we think will be required for the exercise!


<br>**3) Sample Source Data**
<br>There are more features in the address database than we need for workspace construction and testing, so let's reduce that to a smaller sample.

Rather than create a test dataset, here we'll just use a Sampler transformer. So place a Sampler transformer into the Sample Addresses bookmark and connect the PostalAddress feature type to it:

![](./Images/Img3.203.Ex1.SamplerOnCanvas.png)

Inspect the Sampler's parameters. Set it to sample every 25th feature

![](./Images/Img3.204.Ex1.SamplerParams.png)

Add an Inspector transformer (to the Sampler:Sampled output port) and run the workspace to be sure it is sampling the data correctly. Out of 13,597 addresses, there should be 543 selected for use.


<br>**4) Divide Data into Groups**
<br>Before trying to add the Zoning dataset into the workspace, let's try and create groups from the basic dataset. This can be done with a custom transformer from the FME Hub, called the SpatialSorter.

Add a SpatialSorter transformer to the workspace and place it into the Divide Residents bookmark:

![](./Images/Img3.205.Ex1.SpatialSorterOnCanvas.png) 

The SpatialSorter sorts data spatially (so features closer geographically become closer in the sorted output) and creates groups.

Check the parameters for this transformer. Notice that the group parameter asks for a size, not number of groups. Therefore we'll need to calculate how many addresses there are when split into five groups.


<br>**5) Calculate Group Sizes**
<br>To calculate the number of addresses per group, we need the number of addresses and then divide that by five. We can do this with a combination of StatisticsCalculator and ExpressionEvaluator.

So, enlarge the Divide Residents bookmark as required and add a StatisticsCalculator and ExpressionEvaluator transformer. Connect them up to the Sampler:Sampled port like so:

![](./Images/Img3.206.Ex1.StatsExprOnCanvas.png)

 
<br>**6) Calculate Group Sizes**
<br>Inspect the parameters for the StatisticsCalculator. Pick an attribute for the Attributes to Analyze parameter; it can be any attribute, it doesn't matter which.

Under the Total Count Attribute parameter, enter the name TotalResidents. Erase the rest of the calculated attribute fields so they are not calculated.

![](./Images/Img3.207.Ex1.StatsCalcParams.png)

In the ExpressionEvaluator, enter GroupSize in the New Attribute parameter. In the Arithmetic Expression field enter the expression:

	@ceil((@Value(TotalResidents)/5))

![](./Images/Img3.208.Ex1.ExprEvalParams.png)

That expression will divide the number of residents into five groups, rounding up. Add an Inspector transformer to the ExpressionEvaluator and run the translation to prove this part works.


<br>**7) Group Residents**
<br>Now inspect the parameters for the SpatialSorter once more. Change the Grid Size to 256 to give a finer result. Under the Group Size parameter, click the drop-down arrow and select Attribute Value &gt; GroupSize:

![](./Images/Img3.209.Ex1.SpatialSorterParams.png)

This sets the group size to the attribute just calculated. 

To actually create groups of addresses, add an Aggregator transformer to the Group Residents bookmark, and connect it to the SpatialSorter:Sorted output port:

![](./Images/Img3.210.Ex1.AggregatorCanvas.png)

Inspect the parameters for the Aggregator. Set the Group By parameter to the GroupID attribute (created by the SpatialSorter):

![](./Images/Img3.211.Ex1.AggregatorParams.png)

Connect an Inspector (optionally set its Group By parameter to GroupID too) and run the translation. You should find their are five sets of point aggregates in the output, each of which has approximately the same number of point features:

![](./Images/Img3.212.Ex1.AggregatedResults.png)

Save the workspace as GarbageCollection-v1.fmw, or any similar name that includes a version number.

The next step in the workspace will be to add in the Zoning data, create a spatial join, and calculate how many residents live in each property based on each address' zoning type.

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Plan a workspace development</li>
<li>Create a workspace, section by section</li>
<li>Restrict source data to a small sample</li>
<li>Use a custom transformer from the FME Hub</li>
<li>Carry out an arithmetic calculation</li>
<li>Aggregate data into groups</li>
<li>Save a workspace with a version number</li></ul>
</span>
</td>
</tr>
</table>


<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Residential Garbage Collection Zones</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase), Zones (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create boundaries for residential garbage collection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Readers and Writers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex2-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex2-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex2-Complete-Advanced1.fmw</td>
</tr>

</table>

Here we continue on with a project to redefine garbage collection schedules. 

In the first exercise we used various transformers to divide addresses into five separate groups. Now the task is to estimate the number of residents per address based on the zone type it falls within:

- Single-family residences: 2 adults
- Two-family residences: 4 adults
- Multi-family residences: 12 adults
- Comprehensive development zone: 8 adults
- Commercial properties: 1 adult


<br>**1) Open Copy of Workspace**
<br>Make a copy of your original workspace and give it a new version number. For example, if you saved it to GarbageCollection-v1.fmw then make a copy named GarbageCollection-v2.fmw

The idea is that we want to keep version 1 as a checkpoint, in case we need to go back to it at any point.

Open the version 2 workspace in Workbench, ready for editing.


<br>**2) Add Reader**
<br>The first task here is to identify which planning zone each address falls inside. For this we need to read the zoning data and carry out a spatial join. To read a new dataset of data in a different format requires a new reader.

So, select Readers &gt; Add Reader from the menubar. When prompted enter the following parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Zoning\Zones.tab</td>
</tr>

</table>

A reader is added to the Navigator window and a feature type to the canvas. Move the feature type into the Zoning bookmark:

![](./Images/Img3.213.Ex2.ZoningReaderAdded.png) 


<br>**3) Create Spatial Join**
<br>To carry out a spatial join we'll use a PointOnAreaOverlayer transformer; this is a type of join called Point-in-Polygon.

So, add a PointOnAreaOverlayer transformer to the Spatial Join bookmark. Connect the Zoning data to the Area port and the output from the Sampler to the Point port:

![](./Images/Img3.214.Ex2.POAOCanvas.png)

Inspect the parameters and put a check mark against Merge Attributes:

![](./Images/Img3.215.Ex2.POAOParams.png)

This is the first transformer we've used that has a live &lt;Rejected&gt; port. For now we'll leave it to terminate the translation, since during testing we want to know about anything that causes a failure of the transformer.

Attach an Inspector to the Point output port and run the translation. The overlay and attribute merging should cause each address to be given a zone name and category.


<br>**4) Calculate Residents**
<br>The next step is to set how many residents live at a certain address according to its zoning type. 

We know that:

<table>
<tr><th align="center">Zone Begins With</th><th align="center">Zone Type</th><th align="center">Residents</th></tr>
<tr><td align="center">RS</td><td align="center">Single Family</td><td align="center">2</td></tr>
<tr><td align="center">RT</td><td align="center">Two Family</td><td align="center">4</td></tr>
<tr><td align="center">RM</td><td align="center">Multiple Family</td><td align="center">12</td></tr>
<tr><td align="center">CD</td><td align="center">Comprehensive</td><td align="center">8</td></tr>
<tr><td align="center">C</td><td align="center">Commercial</td><td align="center">1</td></tr>
</table>

For example, zones RS-1, RS-2, RS-3 are all single-family zones and we assume a total of two adults per address. This makes it slightly more complex because we need to match a zone type using a "begins with" string comparison.

This can be done in one transformer with an AttributeManager using Conditional Values. 

If you are using the workspace with transformers already defined inside a bookmark, then the AttributeManager is already set up for this purpsoe. Simply move the AttributeManager into the Calculate Residents bookmark and connect it to the PointOnAreaOverlayer:Point output port:

![](./Images/Img3.216.Ex2.AttrManagerCanvas.png)

Then move on to step 5.

Otherwise, if you are not using the predefined transformers, or want to carry out this functionality yourself, place a new AttributeManager transformer as described above.

In the parameters, in the Output Attribute field, create a new attribute called Persons. Click the drop-down arrow in the Attribute Value field and choose Conditional Value:

![](./Images/Img3.217.Ex2.AttrManagerParams.png)

This opens a Tester-like dialog where you can enter multiple conditions. Using this you can set up tests for each zone type, and an attribute value to set them to:

![](./Images/Img3.218.Ex2.AttrManagerConditional.png)

It's important to get these in the correct order, so that "C" comes after "CD", else the results will be incorrect.

---

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
New for FME 2018 is the ability to copy lines from one transformer to another. So to avoid setting this up you could simply open a workspace with the conditions already set, and copy the AttributeManager conditions to the new workspace.
</span>
</td>
</tr>
</table>

---

<br>**5) Create Residents**
<br>We must now apply the number of residents in a way that will affect the output. The simplest way to do this is to create multiple copies of each address. For example, instead of one address with four residents, we'll create four addresses with one resident. 

This can be done very simply with a Cloner transformer. So add a Cloner transformer into the Calculate Residents bookmark. Connect the AttributeManager to its input and its output to the StatisticsCalculator:

![](./Images/Img3.219.Ex2.ClonerCanvas.png)

Inspect the Cloner parameters. For the Number of Copies parameter, click the drop-down arrow and choose Attribute Value &gt; Persons:

![](./Images/Img3.220.Ex2.ClonerParams.png)

This will create *&lt;Persons&gt;* number of duplicate addresses.


<br>**6) Run Translation**
<br>Make sure an Inspector is still attached to the Aggregator transformer and run the translation. The translation will fail with the error message:

<font color="red">

    Cloner_&lt;Rejected&gt;: Termination Message: 'Cloner output a &lt;Rejected&gt; feature.'

</font>
 
This is because addresses without a resident (e.g. Industrial) are being rejected by the Cloner transformer. The &lt;Rejected&gt; port is still set up to terminate the translation and so we get this error.

There are two choices now. We could:

1. Change the Workspace parameter **Rejected Feature Handling** to *Continue Translation*
2. Add a transformer to handle the Cloner's rejected features

Setting the Rejected Feature Handling parameter means all &lt;Rejected&gt; ports would ignore rejected output. This might be useful in a production workspace, but in testing we would probably want to terminate the translation, so we can be aware of issues immediately.

So for us the better solution is to add a transformer to the Cloner &lt;Rejected&gt; port. We don't really need to inspect or log these features because we know that they will exist. So simply connect the &lt;Rejected&gt; port to a small transformer called a Junction:

![](./Images/Img3.221.Ex2.JunctionCanvas.png)

This will handle the rejected output, but quietly drop it without further fuss.

Re-run the translation. The output should be five groups of point feature again, but in a different pattern to the end of the previous exercise:

![](./Images/Img3.222.Ex2.ResidentialResults.png)


<br>**7) Write Output**
<br>Now to write some output. The simplest method is to connect the Aggregator output to the PostalAddress output feature type and re-run the workspace.

However, it would also be useful to rename the output feature type and remove all of its attributes, since they are from the reader dataset and don't really apply here:

![](./Images/Img3.223.Ex2.EditedWriterFT.png)

You'll also want to change the GeoPackage writer parameter to overwrite the database each time we run the workspace:

![](./Images/Img3.224.Ex2.EditedWriterParam.png)

That way we don't accumulate more and more results in the same dataset.

---

<!--Advanced Exercise Section-->

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
The workspace works correctly, but let's say we want to email the output dataset to someone automatically. To do this requires the Emailer transformer. However, the Emailer must appear after the data is written, so first we must replace the writer with a FeatureWriter transformer.
</span>
</td>
</tr>
</table>

<br>**8) Version Workspace**
<br>This is probably a good point at which to save a new version of the workspace, so that if the FeatureWriter doesn't work, we can easily revert to a simple writer.


<br>**9) Add FeatureWriter**
<br>Add a FeatureWriter transformer in place of the writer feature type and connect the Aggregator to it:

![](./Images/Img3.225.Ex2.FeatureWriterCanvas.png)

This will cause an Aggregate port to be added. This becomes the default feature type name in the output.


<br>**10) Set Up FeatureWriter**
<br>Inspect the FeatureWriter parameters. Set the Writer format and dataset to the GeoPackage output dataset already defined:

![](./Images/Img3.226.Ex2.FeatureWriterParameters1.png)

Click the Parameters button and be sure to set the parameter to Overwrite Database:

![](./Images/Img3.227.Ex2.FeatureWriterParameters2.png)

Under the Feature Type definition, rename the output table to GarbageZones:

![](./Images/Img3.228.Ex2.FeatureWriterParameters3.png)

Then click on the User Attributes tab, change the Definition to Manual, and remove all of the attribute definitions (they won't be required):

![](./Images/Img3.229.Ex2.FeatureWriterParameters4.png)

Accept the changes. Now the FeatureWriter is set up to write the data, and you can locate the GeoPackage writer in the Navigator window and delete it.

<br>**11) Add Integration**
<br>If you wish, and if you have an account available, add an Integrations transformer such as the Emailer or the DropboxConnector to the Summary output port of the FeatureWriter. 

Notice that the Summary feature has an attribute called _dataset that defines the dataset written. It can be used in the Emailer (for example) to define a file to be attached to the email:

![](./Images/Img3.230.Ex2.EmailerCanvas.png)

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
In the same way that we can use a FeatureWriter to write data, we could use a FeatureReader to read data. The benefit there is that the spatial join is built into the process.
<br><br>However, we have to consider whether it's useful for us to do here. The current workspace samples the source data before doing a spatial join. A FeatureReader would do the spatial join before sampling, and might therefore be slower. For that reason, we'll avoid doing this for now.
</span>
</td>
</tr>
</table>

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Add a reader to a workspace</li>
<li>Carry out a point-in-polygon spatial join</li>
<li>Set conditional values in an AttributeManager transformer</li>
<li>Use a Cloner transformer to create multiple copies of data</li>
<li>Manage rejected features</li>
<li>Replace a writer with a FeatureWriter</li></ul>
</span>
</td>
</tr>
</table>

<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Residential Garbage Collection Zones</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase), Zones (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create boundaries for residential garbage collection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Readers and Writers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Design-Ex3-Complete.fmw</td>
</tr>

</table>

Here we continue on with a project to redefine garbage collection schedules. 

In the first two exercises we used various transformers to divide addresses into five separate groups, according to zoning type. Then we wrote the data to Geopackage and (optionally) replaced the reader/writer with a FeatureReader/FeatureWriter transformer.

Now the task is simply to replace the groups of point features with a polygon boundary. 


<br>**1) Open Copy of Workspace**
<br>Make a copy of your original workspace and give it a new version number. For example, if you saved it to GarbageCollection-v2.fmw then make a copy named GarbageCollection-v3.fmw

The idea is that we want to keep prior versions as a checkpoint, in case we need to revert at any point.

Open the new version in Workbench, ready for editing.


<br>**2) Run Workspace**
<br>Turn on feature caching using Run &gt; Run with Feature Caching on the menubar.

Now re-run the workspace. The process will take a little longer than the normal translation time, as caches are being created and filled. Take a note of the time taken (1 minute 7 seconds on my machine).

Once complete, click on some caches to prove that the data can be inspected directly in the FME Data Inspector.


<br>**3) Add HullReplacer**
<br>Add a HullReplacer transformer and move it into the Create Boundaries bookmark. Connect it between the Aggregator and FeatureWriter:

![](./Images/Img3.231.Ex3.HullReplacerCanvas.png)

Notice how the HullReplacer has no cache, because it is newly placed.


<br>**4) Re-Run Workspace**
<br>Now let's re-run the workspace. But rather than run the whole translation, click on the HullReplacer transformer and on the icons that pop up, click Run from This:

![](./Images/Img3.232.Ex3.HullReplacerRun.png)

Notice how hovering shows what parts of the workspace will be run. The translation this time should take less than one second, since the results of prior parts of the workspace are already stored in a cache.

The output now includes polygons, to prove that the translation has functioned correctly:

![](./Images/Img3.233.Ex3.HullReplacerOutput.png)


<br>**5) Clean Up Overlaps**
<br>The problem with the output is that all of the polygons overlap to some extent. That needs to be fixed so that there are no overlaps. What's more, we should check to which zone an overlap belongs by seeing which group most of its addresses belong to.

Because this is unexpected, we don't have an area of the workspace set aside yet. So add a new bookmark (or simply move the now-empty Transformers bookmark) and name it Clean Up Overlaps:

![](./Images/Img3.234.Ex3.NewBookmark.png)


<br>**6) Add AreaOnAreaOverlayer**
<br>Overlaps can be dissected using the AreaOnAreaOverlayer transformer, so add one of these to the new bookmark, connected to the HullReplacer transformer. Check the parameters and set the **Attribute Accumulation Mode** to *Drop Incoming Attributes*.

![](./Images/Img3.235.Ex3.AOAOCanvasParams.png)

Re-run the translation by clicking the AreaOnAreaOverlayer and choosing Run From Here. There's no need to add an Inspector transformer because the data can be inspected by simply clicking on the Cache icon.


<br>**7) Add PointOnAreaOverlayer**
<br>The overlaps are dissolved, but we do not yet know which area to assign them to. It should be the one with most addresses; for example if an overlap contains 31 addresses from group one, and 52 addresses from group two, then it should be assigned to the group two polygon. 

We can start on this by using a PointOnAreaOverlayer. This will let us create a list of which addresses an overlap contains.

So add a PointOnAreaOverlayer transformer. The area features will be the output from the AreaOnAreaOverlayer. The point features will be a second connection from the SpatialSorter (i.e. the original points):

![](./Images/Img3.236.Ex3.POAOCanvas2.png)

Inspect the parameters. Under Attribute Accumulation, set the following parameters:

<table>
<tr><td>Merge Attributes</td><td>Yes</td>
<tr><td>Generate List on Output 'Area'</td><td>Yes</td>
<tr><td>'Area' List Name</td><td>PointList</td>
<tr><td>Selected Attributes</td><td>GroupID</td>
</table>

![](./Images/Img3.237.Ex3.POAOParams2.png)

This will create a list of all the point features that fall inside a polygon, with a record of their GroupID values. Confirm this works correctly by running the workspace at the new PointOnAreaOverlayer. Notice how the translation pulls data from two caches; the AreaOnAreaOverlayer and SpatialSorter transformers:

![](./Images/Img3.238.Ex3.POAORun.png)


<br>**8) Add ListHistogrammer**
<br>To count the most frequent ID for records in a list we'll use the ListHistogrammer transformer.

---

<!--Tip Section--> 

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
This is not a commonly used transformer, so don't worry if you weren't aware of it, or if you are concerned about the large number of transformers available in FME. You will learn more about these transformers with practice. For now the ability to use partial runs is much more important. 
</span>
</td>
</tr>
</table>

---

Place a ListHistogrammer transformer connected to the PointOnAreaOverlayer:Area output port. Inspect the parameters and select PointList{}.GroupID as the source attribute:

![](./Images/Img3.239.Ex3.ListHistogrammerCanvas.png)

Re-run the workspace (from the ListHistogrammer) to see the result of this transformer.


<br>**8) Add Dissolver**
<br>Finally let's add a Dissolver to merge the features together. So add a Dissolver connected to the ListHistogrammer output port:

![](./Images/Img3.240.Ex3.DissolverCanvas.png)

Inspect the parameters. Under Group By select the attribute _histogram.value:

![](./Images/Img3.241.Ex3.DissolverParams.png)

You'll be prompted for a value; this is which item in the list do we want. We want the first element because it has the most values, so this field should be set to zero (which it will be by default):

![](./Images/Img3.242.Ex3.DissolverParams2.png)

Re-run the workspace from the Dissolver and inspect the output:

![](./Images/Img3.243.Ex3.DissolverOutput.png)

We now have five polygon features to represent garbage collection areas, each with approximately the same number of residents. Connect the Dissolver:Area port to the writer feature type and this workspace is complete... nearly.


<br>**9) Remove Sampler**
<br>To complete the workspace let's bypass the Sampler transformer and run it on the full dataset, but leaving the Sampler in place in case we need it later. 

To do this first draw a second connection from the source data to the first PointOnAreaOverlayer's Point input port:

![](./Images/Img3.244.Ex3.SamplerBypass.png)

Then right-click on the connection entering the Sampler input and disable it. Now this connection will be ignored. Running the workspace will bypass the Sampler, but leave the Sampler in place for possible later use.

Because this is the first time running this on the full dataset, this is still what we might consider a test of the translation. For this reason leave the Run with Caching option turned on and the Rejected Feature Handling to Terminate.

Once we know the workspace runs without error we can switch these options around for better performance.

As expected, the result will look different, now that we're using the full dataset:

![](./Images/Img3.245.Ex3.SamplerBypassOutput.png)

---

<!--Tip Section--> 

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
On my computer it takes four minutes to run the workspace with caching turned on. Without caching it only takes one minute.
</span>
</td>
</tr>
</table>

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Turn on and use Feature Caching</li>
<li>Use new transformers: HullReplacer, ListHistogrammer, Dissolver</li>
<li>Bypass a transformer by disabling the connection to it</li></ul>
</span>
</td>
</tr>
</table>


