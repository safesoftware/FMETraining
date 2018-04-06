# Data Translation Basics #

At its heart, FME is a data translation tool, and this is usually the first aspect users wish to learn about.

![](./Images/Img1.000.TranslationIntro.png)

# What is FME?
**FME (the Feature Manipulation Engine)** is a data translation and transformation tool for solving problems of data interoperability, without the need for coding.


## Extract, Transform, and Load
FME is sometimes classed as an **ETL** application. ETL stands for Extract, Transform and Load. It is a data warehousing tool that extracts data from multiple sources (here A and B), transforms it to fit the users’ needs and loads it into a destination (C):

![](./Images/Img1.001.WhatIsFME.png)

While most ETL tools process only tabular data, FME also has the processing capabilities required to handle spatial data, hence the term **Spatial ETL**.


## How FME Works ##
At the heart of FME is an engine that supports an array of spatial and tabular data types and formats; GIS, CAD, BIM, Point Cloud, XML, Raster, databases, [and many more](https://www.safe.com/integrate/#!).

The capability to support so many data types is made possible by a rich data model that handles all possible geometry and attribute types. 


![FME: Supported Data Types](./Images/Img1.002.FMEDataTypes.png)


Most importantly, the data translation process is seamless to the user; FME automatically converts between data types as required, and automatically substitutes one attribute or geometry type for another where the destination format does not support it.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Attention students! I'm Miss Vector, FME schoolteacher. I'm here to test you on FME. I hope you don't get these questions wrong!  
<br><br>Q) ETL is an acronym for...?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=1&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Extra-Terrestrial Lifeform</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=1&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Extract, Transform, Load</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=1&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Express Toll Lane</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=1&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Eat, Transform, Love</a>
<br><br>Q) FME can seamlessly translate between so many formats because it has...
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=2&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. A sentient data dictionary</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=2&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. A retro-encabulator</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=2&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. A rich data model</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=2&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. A core of unicorn hairs</a>

</span>
</td>
</tr>
</table>

# FME Desktop #
This course is about FME Desktop. FME Desktop is for data translations and transformations at the desktop level (as opposed to FME Server, which is an enterprise-level, web-based product). 

FME Desktop consists of a number of different tools and applications. The two key applications are **FME Workbench** and the **FME Data Inspector**.

## FME Workbench ##
FME Workbench is the primary tool for defining data translations and data transformations. It has an intuitive point-and-click graphic interface to enable translations to be graphically described as a flow of data.

![](./Images/Img1.003.FMEWorkbench.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

Workbench is not a standalone tool. It is fully integrated to interact with other FME Desktop applications such as the FME Data Inspector.


## FME Data Inspector ##
The FME Data Inspector is a tool for viewing data in any of the FME supported formats. It is used primarily for previewing data before translation or reviewing it after translation.

![](./Images/Img1.004.FMEDataInspector.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

## FME Utilities ##
Besides Workbench and the Data Inspector, there are several other FME utilities.

- **FME Help**
	- A tool for browsing through the various help documents for FME.
- **FME Quick Translator**
	- A precursor to FME Workbench that is used only for quick translations requiring no data transformation.
- **FME Integration Console**
	- A tool for embedding FME functionality into other GIS and CAD applications such as ArcGIS, AutoCAD, Geomedia, and MapInfo.
- **FME Licensing Assistant**
	- An application for managing FME licensing.


## Other FME Desktop Components ##
Additional components are also included as part of FME Desktop (Professional Edition or higher).

- **FME Command Line Engine**
	- The FME Command Line Engine enables translations to be initiated at the command line level.
- **FME Plug-In SDK**
	- The FME Plug-In SDK allows developers to add formats and functionality to the FME core.



# Introduction to FME Workbench #
Let's take a closer look at FME Workbench, firstly how to start it. To start Workbench - besides double-clicking an fmw file - locate Workbench in the Windows start menu:

![](./Images/Img1.005.StartingWorkbench.png)


## Major Components of FME Workbench ##

The FME Workbench user interface has a number of major components:

![](./Images/Img1.006.WorkbenchInterface.png)

### Canvas ###
As we've seen, the FME Workbench canvas is where to define a translation. It is the primary window within Workbench:

![](./Images/Img1.007.WorkbenchCanvas.png)

By default the workspace reads from left to right; data source on the left, transformation tools in the center, and data destination on the right. Connections between each item represent the flow of data and may branch in different directions, merge together, or both.

### Menu/Toolbar ###
The menubar and toolbar contain a number of tools: for example, tools for navigating around the Workbench canvas, controlling administrative tasks, and adding or removing readers/writers:

![](./Images/Img1.008.WorkbenchInterfaceMenuToolbar.png)

### Navigator ###
The Navigator window is a structured list of parameters that represent and control all of the components of a translation:

![](./Images/Img1.009.WorkbenchNavigator.png)

### Transformer Gallery ###
The transformer gallery is a tool for the location and selection of FME transformation tools.

![](./Images/Img1.010.WorkbenchGallery.png)

The number of transformers (above, 484) will vary depending on the version of FME and any optional custom transformers installed:

### Translation Log ###
The translation log reports on translations and other actions. Information includes any warning or error messages, translation status, length of translation, and number of features processed:

![](./Images/Img1.011.WorkbenchLog.png)


<!--### Data Inspection (Visual Preview) Window ###
The Data Inspection window allows visual inspection of data without having to switch to the FME Data Inspection application:

![](./Images/Img1.012.VisualPreview.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.-->

<!--New Section--> 

<!--
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
The Data Inspection window is new for FME2018. As we shall see, it is integrated with various objects on the canvas window to provide seamless data inspection. 
</span>
</td>
</tr>
</table>
-->

### Parameter Editor Window ###
The Parameter Editor window is for editing parameters for objects on the canvas window:

![](./Images/Img1.013.ParameterEditor.png)


As the next section will show, you can open or close these windows at will, or rearrange them into any configuration that you like...

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
As we work through the course the questions will get harder. Still, these are pretty easy: 
<br><br>Which of the following applications is NOT a part of FME Desktop?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=3&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. FME Workbench</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=3&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. FME Integration Console</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=3&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. FME Server Console</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=3&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. FME Data Inspector</a>
<br><br>FME Workbench allows you to define flows of data in which way...
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=4&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Graphically</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=4&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Telepathically</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=4&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Problematically</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=4&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. By writing lots of code in C++ or Java</a>
<br>
</span>
</td>
</tr>
</table>

# Window Control #
All windows in Workbench can be detached from their default position and deposited in a custom location. To do this simply click on the frame of the window and drag it into a new position. 

![](./Images/Img1.014.DraggingWindow.png)

<br>If a window is dropped on top of an existing window, then the two will become **tabbed**.

If a window is dropped beside an existing window (or between two existing windows), then they will become **stacked**.

In the above screenshot the user is dropping the Navigator into position on the left-hand side of Workbench, stacked on top of the Parameter Editor.


<!--Person X Says Section-->

---

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">FireFighter Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Hi. I'm your friendly neighborhood firefighter, with a hot tip for you. Don't feel put out by a lack of canvas space. Press F11 to dispatch lesser-used windows to one side and expand the canvas window to an alarming size!
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Experiment with the Workbench windows (look under the View menu) to answer these questions:
<br><br>Which of these is a window in FME Workbench?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=5&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. The Maths Window</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=5&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. The Geography Window</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=5&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. The English Literature Window</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=5&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. The History Window</a>
<br><br>Which of these is NOT an arrangement of Windows in FME Workbench?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=6&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Stacked</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=6&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Floating</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=6&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Double-Glazed</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=6&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Tabbed</a>
</span>
</td>
</tr>
</table>

# Creating a Translation #

Workbench’s intuitive interface makes it easy to set up and run a simple format-to-format ('quick') translation.

## The Start Tab ##
The Start Tab in FME Workbench includes different ways to create or open a workspace. The simplest method is Generate Workspace:

![](./Images/Img1.015.GettingStarted.png)

## Generate Workspace Dialog ##
The Generate Workspace dialog condenses all the choices to be made into a single dialog box. It has fields for defining the format and location of both the data to be read, and the data to be written.

![](./Images/Img1.016.GenerateWorkspaceDialog.png)

Red coloring in an FME dialog indicates mandatory fields. Users must enter data in these fields to continue. In most dialogs the OK button is deactivated until the mandatory fields are complete.


### Format and Dataset Selection ###

A key requirement is the format of the source data. All format selection fields in FME are both a pull-down menu and a text entry field. 

The text entry field allows you to type a format name directly. It has an 'intelli-complete' function that selects close matches as you type.

The drop-down list shows some of the most commonly used formats, so many favourite formats are instantly available:

![](./Images/Img1.017.FormatSelect.png)

Click 'More Formats' and a table opens showing ALL of the formats supported by FME.

The source dataset is another key requirement. Dataset selection fields are a text entry field, but with a browse button to open an explorer-like dialog for file selection.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Here's a question you can't answer with 'a', 'b', 'c', or 'd'! In the Generate Workspace dialog, why might it be useful to set the data format before browsing for the source data?
<br><br>Try browsing for a dataset before setting the format type and see if you can <a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=7&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">detect the difference.</a>
</span>
</td>
</tr>
</table>

---

## Feature Types Dialog ##
Clicking OK on the Generate Workspace dialog causes FME to generate the defined workspace. However, whenever a source dataset contains multiple layers, the user is first prompted to select which are to be translated.

This is achieved through the Select Feature Types dialog. In FME, ***feature type*** is another term for *layer*. Only selected layers show in the workspace.

![](./Images/Img1.018.FeatureTypeSelect.png)

Here, for example, is a Select Feature Types dialog where the user has chosen to include all available layers in the workspace.


## The New Workspace ##
A new workspace reads from left to right, from the source (Reader) layers, through to the destination (Writer) layers. Arrows denote the direction of data flow:

![](./Images/Img1.019.NewWorkspace.png)

In the above screenshot eight layers are being read from one format and written to another.

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
In most cases FME uses the terms 'Reader' and 'Writer' instead of 'Source’ and ‘Destination.' So a Reader reads datasets and a Writer writes datasets, in terms analogous to source/destination and input/output.
</span>
</td>
</tr>
</table>

---

## Saving the Workspace ##
Workspaces can be saved to a file so that they can be reused at a later date. The save button on the toolbar is one way to do this:

![](./Images/Img1.020.SavingWorkspace.png)

There are also menu options to do the same thing, in this case File &gt; Save (shortcut = Ctrl+S) or File &gt; Save As. The default file extension is .fmw

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Greetings. I am Sister Maria Intuitive of the Order of the Perpetual Translation. I'm here to demonstrate some of the intuitive, but less obvious, features of the FME Workbench interface.
<br><br>For example, select File &gt; Open Recent on the menubar to reveal a list of previously used workspaces. This list can show up to a huge 15 entries.
</span>
</td>
</tr>
</table>

## Running a Workspace ##

The green arrow (or 'play' button) on the Workbench toolbar starts a translation:

![](./Images/Img1.021.RunningWorkspace1.png)

Alternatively, look under Run on the menubar:

![](./Images/Img1.022.RunningWorkspace2.png)

The same toolbar options appear on both the menubar and toolbar. Notice the shortcut option F5 can be used instead: 

![](./Images/Img1.023.RunningWorkspace3.png)

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
The action of the Run button can be modified by a series of options including the ability to prompt the user for input (Run with Prompt), the ability to cache intermediate data (Run with Full Inspection) and the ability to run in debug mode (Run with Breakpoints). These are toggle options that can be turned on and off at will.
</span>
</td>
</tr>
</table>

---
 
## Workspace Results ##
After running a workspace, related information and statistics are found in the translation log, which is displayed in the Workbench log window.

The translation log reveals whether the translation succeeded or failed, how many features were read from the source and written to the destination, and how long it took to perform the translation.

![](./Images/Img1.024.TranslationResults.png)

In this example the log file reveals that 350 features were read (from an Esri Geodatabase) and written out (to a GML dataset).

The overall process was a success, with zero warnings. The elapsed time for the translation was 2.1 seconds.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
I bet you've got all of the questions correct so far! Well done. Now see if you can get these:
<br><br>Which of these is NOT a way to set the format of a translation?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=8&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Typing the format name</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=8&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Selecting the format from a drop-down list</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=8&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Browsing for the format in the formats gallery</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=8&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. By selecting a dataset with a known file extension</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=8&answer=5&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">5. None of the above (they are all valid ways to set the format)</a>
<br><br>Which key is a shortcut to run a workspace?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=9&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. F4</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=9&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. F5</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=9&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. F5.6</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=9&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. F#</a>
</span>
</td>
</tr>
</table>

# Introduction to Data Inspection #

To ensure that you're dealing with the right information you need a clear view of your data at every stage of the transformation process. 

Data Inspection meets this need: it is the act of viewing data for verification and debugging purposes, before, during, or after a translation.

## What Can Be Inspected? ##
A number of different aspects of data may be inspected, including the following:

- **Format**: Is the data in the expected format?
- **Schema**: Is the data subdivided into the correct layers, categories or classes?
- **Geometry**: Is the geometry in the correct spatial location? Are the geometry types correct?
- **Symbology**: Is the color, size, and style of each feature correct?
- **Attributes**: Are all the required attributes present? Are all integrity rules being followed?
- **Quantity**: Does the data contain the correct number of features?
- **Output**: Has the translation process restructured the data as expected?

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Chef Bimm says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Hi. I'm Chef Bimm and I'm here to help you cook up some tasty data translations.
<br><br>I have a great recipe for loading CAD files into a Building Information Model. Inspecting the ingredients... I mean data... before I use them lets me detect problems before they affect the translation.
<br><br>Features in the wrong source layer could need the whole process to be repeated. Data Inspection saves me that hassle. Now I know that if the "sauce" is fine, the final result will be too!
</span>
</td>
</tr>
</table>

# Introduction to the FME Data Inspector #

The easiest place to start inspecting data in FME is in a complementary application called the FME Data Inspector.

## What is the FME Data Inspector? ##
The FME Data Inspector is a utility that allows viewing of data in any of the FME supported formats. It is used primarily to preview data before translation or to verify it after translation. 

The FME Data Inspector is closely tied to FME Workbench so that Workbench can send data directly to the Inspector. It's also embedded inside FME Workbench too, to help set up and debug workspaces by inspecting data *during* the translation.

## What the FME Data Inspector Is Not! ##
The FME Data Inspector isn’t designed to be a form of GIS or mapping application. It has no analysis functionality and the tools for symbology modification or printing are intended for data validation rather than producing map output.

## Starting the FME Data Inspector ##
To start the Data Inspector locate it in the Windows start menu:

![](./Images/Img1.025.StartingDataInspector.png)


## Major Components of the FME Data Inspector ##

When the FME Data Inspector is started, and a dataset is opened, it looks something like this:

![](./Images/Img1.026.InspectorInterface.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

### View Window ###
The View window is the spatial display area of the FME Data Inspector. Multiple views of different datasets may be opened at any one time.

![](./Images/Img1.027.DataInspectorViewWindow.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

## Menu bar and Toolbar ###
The menu bar and toolbar contain a number of tools. Some are for navigating around the View window, some control administrative tasks such as opening or saving a dataset, and others are for special functionality such as selective filtering of data or the creation of dynamic attributes.

![](./Images/Img1.028.DataInspectorToolbar.png)

### Display Control Window ###
The Display Control window shows a list of the open datasets and their feature types. Tools here let users turn these on or off in the display, alter their symbology, and adjust the display order.

![](./Images/Img1.029.DataInspectorDisplayControlWindow.png)

### Feature Information Window ###
When users query a feature in the View window, information about that feature is shown in the Information window. This information includes the feature’s feature type, attributes (both user and format attributes), coordinate system and details about its geometry.

![](./Images/Img1.030.DataInspectorFeatureInformation.png)

### Table View Window ###
The Table View window is a spreadsheet-like view of a dataset and includes all of the features and all of the attributes, with a separate tab for each feature type (layer).

![](./Images/Img1.031.DataInspectorTableView.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
FME is so easy to use, it's hard to think up some difficult questions! But I'll try.
<br><br>When you are inspecting <strong>schema</strong>, what are you trying to verify?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=10&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. The color and linestyle of features</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=10&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. The number of features</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=10&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. The feature types (layers, classes, tables) and their attributes</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=10&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Where the nearest coffee shop is</a>
</span>
</td>
</tr>
</table>

# Using the FME Data Inspector #

With the FME Data Inspector it’s easy to open and view any number of datasets and to query features within them.

 
## Viewing Data ##
The FME Data Inspector provides two methods for viewing data: opening or adding. 

***Opening*** a dataset opens a new view window for it to be displayed in. ***Adding*** a dataset displays the data in the existing view window; this way multiple datasets can be viewed simultaneously.

### Opening a Dataset ###
Datasets can be opened in the FME Data Inspector in a number of ways.

- Select File > Open Dataset from the menu bar
- Select the toolbar button Open Dataset.
- Drag and drop a file onto any window (except the View window)
- Open from within Workbench

![](./Images/Img1.032.DIOpenDataset.png)

Opening data from within FME Workbench is achieved by simply right-clicking on a canvas feature type (either source or destination) and choosing the option ‘Inspect'.

All of these methods cause a dialog to open in the FME Data Inspector in which to define the dataset to view.

![](./Images/Img1.033.DIOpenDatasetDialog.png)

### Adding a Dataset ###
Opening a dataset causes a new View tab to be created and the data displayed. To open a dataset within an existing view tab requires use of tools to add a dataset.

- Selecting File > Add Dataset from the menu bar
- Selecting the toolbar button Add Dataset
- Dragging and Dropping a file onto the view window

![](./Images/Img1.034.DIAddDataset.png)

### Windowing Tools ###
Once data has been opened in the FME Data Inspector, there are a number of tools available for altering the view.

- Pan
- Zoom In
- Zoom Out
- Zoom to a selected feature
- Zoom to the full extent of the data

![](./Images/Img1.035.DIWindowTools.png)

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
Press the Shift key on the keyboard and it will activate the zoom-in tool in the Inspector.
Press the Ctrl key and it will activate the zoom-out tool. Release the key to revert to the previous tool.
<br><br>
This functionality allows users to quickly move between query and navigation modes at the press of a key, so there's no need to click between query and navigation tools on the menubar or toolbar.
</span>
</td>
</tr>
</table>

## Inspecting Data ##
The FME Data Inspector includes several querying tools, but two are particularly important:

- Query individual feature(s)
- Measure a distance within a View window

![](./Images/Img1.036.DIQueryTools.png)

The query tool button is like a toggle. By default it is active when you start the FME Data Inspector; if you click it again - or select a windowing tool - you turn the query tool off. 

The results of a feature query are shown in the Feature Information window.


### Feature Information Window ###
The upper part of this window reports on general information about the feature; which feature type (layer/table) it belongs to, which coordinate system it is in, whether it is two- or three-dimensional, and how many vertices it possesses.

<!--Repeat of Image 30--> 
![](./Images/Img1.030.DataInspectorFeatureInformation.png)

The middle part reports the attributes associated with the feature. This includes user attributes and format attributes (for example *fme_type*).

The lower part reports the geometry of the feature. It includes the geometry type and a list of the coordinates that go to make up the feature.


### Table View Window ###
Also available is a window called the Table View.

<!--Repeat of Image 31--> 
![](./Images/Img1.031.DataInspectorTableView.png)

The table view is a way to inspect data in a tabular, spreadsheet-like, layout. Although it does not have the same depth of information shown by the Information Window, the Table View is particularly useful for inspecting the attribute values of multiple features simultaneously.

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
To improve performance, tables are not all displayed automatically, only when selected from the drop-down list, or when queried in the current view window.
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Start the FME Data Inspector and open a dataset. In the Table View window right-click on records and column-headers to view the context menus. Which of the following is NOT an available menu option(s): 
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=11&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Sort (Alphabetical or Numeric)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=11&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Inspect Value</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=11&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Cut/Copy/Paste</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=1&question=11&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Save Selected Data As</a>
</span>
</td>
</tr>
</table>


## Data Inspector Display Control ##

The FME Data Inspector has a number of controls to assist in showing the data in an orderly manner.

 
### Display Control Window ###
Management of feature display order is carried out in the Display Control window.

Each dataset and feature type can be dragged above any other to promote its display order in the View window:

![](./Images/Img1.037.DIDisplayControl.png)

Feature Types can only be ordered within their container dataset.

For example, "Libraries" can be promoted above "GarbageSchedule" in the display, but they cannot by themselves be promoted above the separate Parks dataset.

---

### Display Status ###
Each level of the Display Control window has a checkbox to turn data on and off at that level:

![](./Images/Img1.038.DIDisplayStatus.png)

You can choose to turn off individual layers or an entire dataset at once.

---

### Feature Counts ###

Each Feature Type in the Display Control window is tagged with the number of features it contains, in parentheses after the feature type name. So in the previous image we can see that there are 113 drinking fountains (or 113 features called DrinkingFountains) in the city of Vancouver.

Clicking a feature count selects all of those features for display in the Feature Information and Table View windows, and also activates the tool File > Save Selected Data As:

![](./Images/Img1.039.DILinkedCounts.png)

---

### Style ###

Each feature type can be assigned a different color or style that applies to its geometries. To access this functionality click on the style icon for that feature type in the Display Control window:

![](./Images/Img1.040.DIStylePick.png)

The Drawing Style dialog allows you to set all manner of symbology for a feature. That includes feature color (and degree of transparency), point icon/symbol, point size, line thickness, etc:

![](./Images/Img1.041.DIStyleSet.png)

Notice that the dialog only displays symbology options for the type of geometry available. Here it is for a polygon feature. Other geometry types display different options. 

## Background Maps ##

The ability to view maps (or other imagery) as a backdrop to your spatial data is activated by a tool under Tools > FME Options on the menubar.

The background map dialog lets the user select an existing dataset (of any FME-supported format) to use as a backdrop, like so:

![](./Images/Img1.042.DIBackgroundDialog.png)

It's also possible to use a number of different web services that supply mapping on demand. Some of these - such as ArcGIS Online - do require an existing account:

![](./Images/Img1.043.DIBackgroundServices.png)


### Coordinate Systems ###

To view against a background map, source data must be referenced against a valid coordinate system. If the coordinate system is not recorded in the dataset itself, you may enter it into a field when opening the dataset:

![](./Images/Img1.044.DICoordinateSystem.png)

FME is able to display the source data against a background map, even when there are several source datasets of differing coordinate systems. FME does this by reprojecting the data to the coordinate system used by the background map. Therefore it's recommended that you turn off the background maps when you want to inspect the data in its original form. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police Chief Webb-Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
You can adjust the symbology and display order of the background map in the Display Control window, just as you can for any normal dataset.
</span>
</td>
</tr>
</table>


# Reader Parameters ##
As we know, a workspace contains a reader to read a dataset, and each layer in that dataset is shown in the workspace canvas: 

![](./Images/Img1.045.ReaderFTs.png)

To control how that reader operates requires the use of **reader parameters**.


### Finding Reader Parameters ###
Reader parameters can be located - and set - by clicking Parameters when a new workspace is being generated:

![](./Images/Img1.046.ReaderParamsGen.png)

They can also be found in the Navigator window in Workbench:

![](./Images/Img1.047.ReaderParamsNav.png)

Because parameters refer to specific components and characteristics of the related format, readers of different formats have a different set of control parameters.


### Setting Reader Parameters ###
To edit a parameter in the Navigator window, double-click on any of the parameters. This opens up a dialog where the parameter’s value may be set:

![](./Images/Img1.048.ReaderParamsSet.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Reader parameters control all feature types in the dataset. Think of it like brewing a pot of coffee. The strength control on the coffee machine affects all the cups that are poured. 
</span>
</td>
</tr>
</table>

## Writer Parameters ##
Like readers, we know a workspace contains a writer to write a dataset, and each layer to be written is shown in the workspace canvas: 

![](./Images/Img1.049.WriterFTs.png)

To control how that writer operates requires the use of **writer parameters**.


### Finding Writer Parameters ###
Writer parameters can be located - and set - by clicking Parameters when a new workspace is being generated:

![](./Images/Img1.050.WriterParamsGen.png)

They too can also be found in the Navigator window in Workbench:

![](./Images/Img1.051.WriterParamsNav.png)

Because parameters refer to specific components and characteristics of the related format, writers of different formats have a different set of control parameters.


### Setting Writer Parameters ###
To edit a parameter in the Navigator window, double-click on any of the parameters. This opens up a dialog where the parameter’s value may be set:

![](./Images/Img1.052.WriterParamsSet.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Like readers, writer parameters control all feature types in the dataset. For example, in the above screenshot, all feature types will be version 3.1.1.
<br><br>But each reader and writer feature type does have its own settings (in the same way that each cup of coffee can be adjusted with cream and sugar). We'll find out about that in the next chapter. 
</span>
</td>
</tr>
</table>

# Module Review #

This module introduced you to FME and investigated the basics of FME data translations.

 
## What You Should Have Learned from this Module ##

The following are key points to be learned from this session:

### Theory ###

- FME is a tool to translate and transform data, with an emphasis on spatial data. 

- FME Workbench is an application to graphically define a translation and the flow of data within it. The definition of a translation is known as a *workspace* and can be saved to a file for later use.

- Quick Translation is the technique of carrying out a translation generated by FME, without further editing.

- The Generate Workspace dialog is the main method by which a *quick translation* can be set up in FME Workbench.

- Data Inspection is a technique for checking and verifying data before, during, and after a translation. The FME Data Inspector is a tool for inspecting data.


### FME Skills ###

- The ability to open a workspace in FME Workbench and run it
- The ability to start FME Workbench and set up a *quick translation*
- The ability to start the FME Data Inspector, and to open and add datasets
- The ability to navigate a dataset and to query features within it
- The ability to control Data Inspector symbology and display characteristics
- The ability to set background maps in the Data Inspector

### Further Reading ###

For further reading why not browse **[articles about data formats](http://blog.safe.com/tag/data-formats)** or **[articles tagged with Data Inspector](http://blog.safe.com/tag/data-inspector)** on our blog? 


# Questions #

Here are the answers to the questions in this chapter.


---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
ETL is an acronym for...?
<br><br><span style="color:lightslategrey">1. Extra-Terrestrial Lifeform</span>
<br><span style="font-weight:bold">2. Extract, Transform, Load</span>
<br><span style="color:lightslategrey">3. Express Toll Lane</span>
<br><span style="color:lightslategrey">4. Eat, Transform, Love</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
FME can seamlessly translate between so many formats because it has...
<br><br><span style="color:lightslategrey">1. A sentient data dictionary</span>
<br><span style="color:lightslategrey">2. A retro-encabulator</span>
<br><span style="font-weight:bold">3. A rich data model</span>
<br><span style="color:lightslategrey">4. A core of unicorn hairs</span>
</span>
</td>
</tr>
</table>

---
<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which of the following applications is NOT a part of FME Desktop?
<br><br><span style="color:lightslategrey">1. FME Workbench</span>
<br><span style="color:lightslategrey">2. FME Integration Console</span>
<br><span style="font-weight:bold">3. FME Server Console</span>
<br><span style="color:lightslategrey">4. FME Data Inspector</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
FME Workbench allows you to define flows of data in which way...
<br><br><span style="font-weight:bold">1. Graphically</span>
<br><span style="color:lightslategrey">2. Telepathically</span>
<br><span style="color:lightslategrey">3. Problematically</span>
<br><span style="color:lightslategrey">4. By writing lots of code in C++ or Java</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which of these is a window in FME Workbench?
<br><br><span style="color:lightslategrey">1. The Maths Window</span>
<br><span style="color:lightslategrey">2. The Geography Window</span>
<br><span style="color:lightslategrey">3. The English Literature Window</span>
<br><span style="font-weight:bold">4. The History Window</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which of these is NOT an arrangement of Windows in FME Workbench?
<br><br><span style="color:lightslategrey">1. Stacked</span>
<br><span style="color:lightslategrey">2. Floating</span>
<br><span style="font-weight:bold">3. Double-Glazed</span>
<br><span style="color:lightslategrey">4. Tabbed</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Q) In the Generate Workspace dialog, why might it be useful to set the data format before browsing for the source data?
<br><br><span style="font-weight:bold">A) Because then the explorer dialog only displays files whose extension matches the format type</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which of these is NOT a way to set the format of a translation?
<br><br><span style="color:lightslategrey">1. Typing the format name</span>
<br><span style="color:lightslategrey">2. Selecting the format from a drop-down list</span>
<br><span style="color:lightslategrey">3. Browsing for the format in the formats gallery</span>
<br><span style="color:lightslategrey">4. By selecting a dataset with a known file extension</span>
<br><span style="font-weight:bold">5. None of the above (they are all valid ways to set the format)</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which key is a shortcut to run a workspace?
<br><br><span style="color:lightslategrey">1. F4</span>
<br><span style="font-weight:bold">2. F5</span>
<br><span style="color:lightslategrey">3. F5.6</span>
<br><span style="color:lightslategrey">4. F#</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
When you are inspecting <strong>schema</strong>, what are you trying to verify?
<br><br><span style="color:lightslategrey">1. The color and linestyle of features</span>
<br><span style="color:lightslategrey">2. The number of features</span>
<br><span style="font-weight:bold">3. The feature types (layers, classes, tables) and their attributes</span>
<br><span style="color:lightslategrey">4. Where the nearest coffee shop is</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Start the FME Data Inspector and open a dataset. In the Table View window right-click on records and column-headers to view the context menus. Which of the following is NOT an available menu option(s): 
<br><br><span style="color:lightslategrey">1. Sort (Alphabetical or Numeric)</span>
<br><span style="color:lightslategrey">2. Inspect Value</span>
<br><span style="font-weight:bold">3. Cut/Copy/Paste</span>
<br><span style="color:lightslategrey">4. Save Selected Data As</span>
</span>
</td>
</tr>
</table>

<!--Exercise Section-->

<!--This exercise assumes that Caching and Embedded Inspection are both turned OFF by default. If this is not the case then it may need adjusting to take account of those features.-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Opening and Running a Workspace</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Libraries (Esri Geodatabase)<br>Roads (AutoCAD DWG)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">To open and run an FME workspace to explore what it can do with data</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Opening and running a workspace</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Basics-Ex1-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

</table>


Rather than trying to explain what FME is and does, let's try it for ourselves!


**1) Locate Workspace File**
<br>When translations and transformations are defined in FME, they can be saved in a .fmw file.

Using a file explorer, browse to the file listed above

![](./Images/Img1.200.Ex1.LocateWorkspace.png)

Double-click on the file. It will open an application called FME Workbench.


<br>**2) Explore FME Workspace**
<br>In FME Workbench, dismiss any Getting Started dialog that may open by clicking "Don't Show Me Again."

The main part of the application will look like this:

![](./Images/Img1.201.Ex1.OpenedWorkspace.png)

This part we call the canvas. It is where the translation and transformation of data is defined graphically. Although it might look complicated, it does not take much practice with FME to create workflows of this type.

Examine the left-hand side of the canvas:

![](./Images/Img1.202.Ex1.BookmarkedReader.png)

This is where we read data, in this case a table of libraries from an Esri Geodatabase. This is the "E" (Extract) part of ETL.

Now look at the right-hand side:

![](./Images/Img1.203.Ex1.BookmarkedWriter.png)

This is where we write data, in this case a report of the libraries in HTML format. This is the "L" (Load) part of ETL.

In between the reader and writer are objects that transform data. They represent the "T" (Transform) part of ETL.

Labels and other annotations show us what the workspace does. It:

- Reads both roads (AutoCAD DWG) and libraries (Esri Geodatabase)
- Calculates the shortest road route taking in all libraries
- Creates circles whose diameter is relative to a library's book circulation
- Creates a HTML report and a HTML map of the libraries
- Writes the data to HTML and also to Esri Shapefile

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police-Chief Webb-Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
I'm the police chief, responsible for tracking down crimes against FME. 
<br><br>So, let's make sure you get the terminology right. The application itself is called FME "Workbench", but the process defined in the canvas window is called a "Workspace". The terms are so similar that they are easily confused, but please don't, otherwise I will have to send my grammar squad to arrest you! 
<br><br>Although mistreating FME terminology is a minor offence, the ignominy of being caught is long lasting!

</span>
</td>
</tr>
</table>

---

<br>**3) Run FME Workspace**
<br>Let's run this workspace. To do this click on the Green run button on the Workbench toolbar:

![](./Images/Img1.204.Ex1.RunButton.png)

The workspace will now run. As it does so you will see messages pass by in a log window. You may also see numbers appear on the canvas connections and green annotated icons on each object. We'll get to what these are for later!


<br>**4) Locate and Examine Output**
<br>Once the translation is complete, click on the HTML writer object on the canvas. Choose the option to Open Containing Folder:

![](./Images/Img1.205.Ex1.OpenContainingFolder.png)

In the Explorer dialog that opens you will find both the HTML output and the Shapefile dataset:

![](./Images/Img1.206.Ex1.OutputFiles.png)

Open a web browser such as Firefox or Chrome. Open the output file created by FME (usually Ctrl+O or File &gt; Open is the easiest way). You will see a table of libraries, a graph of library statistics, and an interactive map showing where the libraries are located. All this has been generated by FME from the incoming Geodatabase points and attributes:

![](./Images/Img1.207.Ex1.HTMLOutput.png)


<!--Person X Says Section-->

---

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
This small demonstration illustrates the power of FME. This workspace read data from multiple spatial datasets and wrote it out to datasets in both spatial and "tabular" formats. In between it carried out a series of transformations and spatial analyses, buffering and reprojecting the data, and creating added value and information.
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
<ul><li>Open an FME workspace</li>
<li>Run an FME workspace</li>
<li>Locate the output from an FME workspace</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Basic Workspace Creation</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Zoning Data (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to translate zoning data in MapInfo TAB format to GeoJSON (Geographic JavaScript Object Notation)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Basic workspace creation with FME Workbench</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Basics-Ex2-Complete.fmw</td>
</tr>

</table>


Congratulations! You have just landed a job as technical analyst in the GIS department of your local city. Your old schoolteacher, Miss Vector, gave you a reference, so don't let her down! 

On your first day you've been asked to do a simple file format translation. 

We’ve outlined all of the actions you need to take; though FME's interface is so intuitive you should be able to carry out the exercise without the need for these step-by-step instructions. 


**1) Start FME Workbench**
<br>If it isn't open already, start FME Workbench by selecting it from the Windows start menu. You’ll find it under Start > FME Desktop 2018.0 > FME Workbench 2018.0.

If Workbench is already open, click on the Start tab above the main canvas.

<br>**2) Select Generate Workspace**
<br>In the Create Workspace part of the Start page select the option to Generate (Workspace). Alternatively you can use the shortcut Ctrl+G. 

<!--Repeat of Image 15--> 
![](./Images/Img1.015.GettingStarted.png)


<br>**3) Define Translation**
<br>The Generate Workspace tool opens up a dialog in which to define the translation to be carried out. Fill in the fields in this dialog as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Zoning\Zones.tab</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">GeoJSON (Geographic JavaScript Object Notation)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training\Zones.json</td>
</tr>

</table>

The dialog will look like this:

![](./Images/Img1.208.Ex2.GenerateWorkspaceDialog.png)

Remember, you can set a format by typing its name, by selecting it from the drop- down list, or by choosing “More Formats” and selecting the format from the full table of formats. For now, ignore the Workflow Options and leave the default of 'Static Schema.'


<br>**4) Generate and Examine Workspace**
<br>Click OK to close the Generate Workspace dialog. A new workspace will be generated into the FME Workbench canvas: 

![](./Images/Img1.209.Ex2.NewWorkspace.png)

The list of attributes is exposed by clicking the arrow icon on each object.


<br>**5) Run Workspace**
<br>Run the workspace by clicking the run button on the toolbar, or by using Run > Run Translation on the menubar. The workspace runs and the log file reports a successful translation:

![](./Images/Img1.210.Ex2.LogWindow.png)



<br>**6) Locate Output**
<br>Locate the destination data in Windows Explorer to prove that it's been written as expected (don't forget the Open Containing Folder button from Exercise 1). In the next section we’ll cover how to inspect the dataset visually to ensure that it is correct.

![](./Images/Img1.211.Ex2.JSONInExplorer.png)


<br>**7) Save Workspace**
<br>Save the workspace. We'll be using it in a later exercise. Remember there is a toolbar save button and on the menu there is File &gt; Save As.

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
When a translation is run immediately without adjustment it's known as a "Quick Translation". Because FME is a 'semantic' translator, with an enhanced data model, the output from a quick translation is as close to the source data in structure and meaning as possible, given the capabilities of the destination format.
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
<ul><li>Create an FME workspace</li>
<li>Run an FME workspace</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Basic Data Inspection</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Zoning Data (GeoJSON)<br>Neighborhoods (Google KML)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Inspect the output from a previous translation</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Basic data inspection with the FME Data Inspector</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

</table>


In the previous exercise you were asked to convert some data between formats. Before you send the converted data out you should really inspect it to make sure it is correct. Let’s see how the FME Data Inspector interface works by inspecting the output from that quick translation.


**1) Start FME Data Inspector**
<br>Start the FME Data Inspector by selecting it from the Windows start menu. You’ll find it under Start > FME Desktop 2018.0 > FME Data Inspector 2018.0.


<br>**2) Open Dataset**
<br>The FME Data Inspector will start up and begin with an empty view display.

To open a dataset, select File > Open Dataset from the menubar.
When prompted, fill in the fields in the Select Dataset dialog as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">GeoJSON (Geographic JavaScript Object Notation)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Output\Training\Zones.json</td>
</tr>

</table>

***NB:*** *If you can't find the dataset - maybe you didn't complete the first exercise, or wrote the data to a different location - then you can open the original zoning dataset as described in Exercise 2.*

The GeoJSON dataset looks like this:

![](./Images/Img1.212.Ex3.DataInspectorDataView.png)


<br>**3) Browse Data**
<br>Use the windowing tools on the toolbar to browse through the dataset, inspecting it closely. Use the Query tool to query individual features and inspect the information in the Feature Information Window.

Try right-clicking in the different Data Inspector windows, to discover functionality that exists on context menus.


<br>**4) Add Dataset**
<br>Let's add a second dataset to the display to reference our zoning data against. This dataset will be a KML file of neighborhood boundaries. Then we'll be able to see which neighborhood each zone overlaps.

To add a dataset, select File > Add Dataset from the menubar. When prompted, fill in the fields in the Select Dataset dialog as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Google KML</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Boundaries\VancouverNeighborhoods.kml</td>
</tr>

</table>

The display now looks like this:

![](./Images/Img1.213.Ex3.DataInspectorAddedDataView.png)

Although this looks confusing, there are methods that can be used to clean up the display, as we shall find shortly...

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
Similar to the above, you can locate the output dataset by clicking the pop-up option to Open Containing Folder. 
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
<ul><li>Open datasets in a new view in the FME Data Inspector</li>
<li>Use the windowing and inspection tools in the FME Data Inspector</li>
<li>Use FME Workbench functionality to open a dataset in the FME Data Inspector</li></ul>
</span>
</td>
</tr>
</table>


<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">The FME Data Inspector</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Zoning Data (GeoJSON)<br>Neighborhoods (Google KML)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Set up layer and dataset display</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Use of Display Control and Background Maps in the Data Inspector</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Basics-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Basics-Ex4-Complete.fmw </td>
</tr>

</table>


In the previous exercise we inspected some data from a translation and added a second dataset. Now we can rearrange the data to make the display clearer.


<br>**1) Start FME Data Inspector**
<br>Continue in the FME Data Inspector from the previous exercise. You should have both the converted zones data (as GeoJSON) and a dataset of neighborhood boundaries in KML. The Display Control window looks like this:

![](./Images/Img1.214.Ex4.DisplayControlWindow.png)


<br>**2) Set Neighborhoods Symbology**
<br>The Display Control window shows a number of different layers in the VancouverNeighborhoods dataset. In reality most of these are tabular (non-spatial) items. The layer we are really interested in is called Neighborhoods.

Click the symbology icon for the Neighborhoods data in the Display Control window:

![](./Images/Img1.215.Ex4.SetSymbologyIcon.png)

Set the color to be a neutral shade (like orange) and increase the opacity value to 0.8:

![](./Images/Img1.216.Ex4.SetSymbologyDialog.png)


<br>**3) Set Draw Order**
<br>The previous change makes it clear that the zone features are below the neighborhoods in the drawing order. To solve this problem drag the Zones dataset above the VancouverNeighborhoods dataset in the Display Control Window.

At the same time set a color for the zones data fill color and reduce the opacity value to 0.1. The main view will now look like this:

![](./Images/Img1.217.Ex4.ResymbolizedData.png)

If you query a zone feature you'll see that it has both a ZoneCategory and ZoneName attribute. You might not realize, but there is a relationship between those attributes. Each ZoneName belongs to a specific ZoneCategory, where Category:Name is a 1:Many relationship.

Let's clarify the display by merging all the features into one feature per ZoneCategory. We can do that in FME Workbench.
 

<br>**4) Return to Workspace**
<br>Return to FME Workbench. Open the workspace saved in Exercise 2, or the workspace listed above. 

What we'll do here is use what we call a transformer. This is something we'll cover in more detail in the chapter on Data Transformation. Basically it is an object to transform data in some way.

Click on the dark line connecting the Reader Feature Type and Writer Feature Type. Start typing the word "Dissolver":

![](./Images/Img1.218.Ex4.AddTransformer.png)

When you see the Dissolver transformer appear in the list, double-click on it to place it into the workspace. The result will look like this:

![](./Images/Img1.219.Ex4.DissolverTransformer.png)

The Dissolver parameter will merge together all features with a common attribute value.


<br>**5) Set Dissolver Parameters**
<br>Click on the little cogwheel icon on the Dissolver transformer (it will probably be yellow in color):

![](./Images/Img1.220.Ex4.DissolverParametersButton.png)

This will open a parameters dialog for the transformer. Click the elipsis (...) button next to the Group By parameter. In the dialog that opens select the ZoneCategory attribute and click OK.

![](./Images/Img1.221.Ex4.DissolverGroupByParameter.png)

Click OK again to close the parameters dialog. 

Save the workspace and run it once more. The translation will run and the data be overwritten.


<br>**6) Refresh Data Inspector View**
<br>Back in the Data Inspector, rather than reopening the data, let's refresh the view of it. To do so click the Refresh button on the toolbar:

![](./Images/Img1.222.Ex4.DIRefreshView.png)

You'll now find there are fewer features, as many have been merged together.


<br>**7) Set Background**
<br>When inspecting data it will help to have a background map to provide a sense of location. The FME Data Inspector is capable of displaying a backdrop from several different mapping services.

Select Tools > FME Options from the menubar. In the Background Map section, select a background map format. If you have an account with a specific provider, please feel free to use that. Otherwise select Stamen Maps:

![](./Images/Img1.223.Ex4.BackgroundMapDialog.png)

Click the Parameters button. A map constraint (type) dialog will open. Click the browse button and select "terrain":

![](./Images/Img1.224.Ex4.BackgroundMapPropertiesDialog.png)

Click OK and OK again to close these dialogs. A background map is added to the display. Notice that the data is reprojected to match the coordinate system of the chosen background. For example, the Stamen Maps background causes the data to reproject to Spherical Mercator, with a clear change of shape:

![](./Images/Img1.225.Ex4.DataWithBackgroundMap.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.


<!--<br>**8) Filter Data**
<br>Let's try something to filter our data a little in the Data Inspector.

Choose Tools &gt; Filter Features from the menubar, or click the toolbar button for filters:

![](./Images/Img1.226.Ex4.FilterButton.png)

In the Filter Features dialog, double click in the Left Value field, click the drop down arrow, and select Attribute Value. Choose ZoneCategory as the attribute to filter by and click OK.

For the Operator field select the = (equals) symbol, if it is not already selected.

For the Right Value field, click in the field and type the word **Industrial** (don't worry, it's not case-sensitive).

![](./Images/Img1.227.Ex4.OneFilterSet.png)

Filtering in the Data Inspector is applied to all visible data (if you clicked OK now the Neighborhood data would also be filtered out) therefore we must also add a clause to enable the neighborhood data to remain on screen.

Create a second test clause using the same techniques as before. This time select the attribute NeighborhoodId and select the operator **Attribute has a value**:

![](./Images/Img1.228.Ex4.TwoFiltersSet.png)

The Pass Criteria parameter should be set (or left as) "One Test (OR)".

![](./Images/Img1.229.Ex4.DIFilterCriteria.png)

Now click OK to close the dialog. The display will be filtered to show only the neighborhood features plus zones of type industrial:

![](./Images/Img1.230.Ex4.FilteredData.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

The Display Control Window will also show the effects of the filter:

![](./Images/Img1.231.Ex4.DisplayControlFilter.png)


<br>**9) Set Writer Parameters**-->
<br>**8) Set Writer Parameters**
<br>One final task: the output GeoJSON file is intended for distribution via the internet, and you've been asked to make the file size as small as possible. Check the current file size. It will be approximately 362kb.

There are a couple of writer parameters that can be used to reduce GeoJSON file size.

Explore the Navigator window in FME Workbench, and look for the GeoJSON writer parameters. Double-click on one of the parameters, such as Formatting Type:

![](./Images/Img1.231a.Ex4.WriterParameters.png)

In the dialog that opens, set the Formatting Type to Linear and the Coordinate Precision to 6:

![](./Images/Img1.231b.Ex4.SettingWriterParameters.png)

Re-run the workspace. You should find that the results are the same, but the file size is now closer to 232kb.

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
<ul>
<li>Set symbology for features in the FME Data Inspector</li>
<li>Set a background map for the FME Data Inspector</li>
<li>Add a transformer in FME Workbench and set its parameters</li>
<li>Refresh the Data Inspector when source data is updated</li>
<!--<li>Filter data using test clauses in the FME Data Inspector</li>-->
<li>Set writer parameters in the Navigator window</li></ul>
</span>
</td>
</tr>
</table>


<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Tourist Bureau Project</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Community Mapping/Food Vendors (Esri Geodatabase)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a GPS-compatible dataset of food vendors for the local tourist bureau</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Basic Data Translation and Data Inspection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Basics-Ex5-Complete.fmw</td>
</tr>

</table>


You've barely started in your new job, but requests are coming in fast! 

The local tourist bureau is running a promotion where they provide tourists with a GPS device to help them visit street food vendors in the city. Your manager wonders whether you can use FME to produce the data to be used in this scheme.

Let's get onto that right away shall we?


<br>**1) Start FME Workbench**
<br>Start FME Workbench. In the Create Workspace section of the Start window, choose the option to Generate (Workspace). When prompted generate a translation with the following parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Esri Geodatabase (File Geodb Open API)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\CommunityMapping\CommunityMap.gdb</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">GPS eXchange Format (GPX)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training\FoodVendors.gpx</td>
</tr>

</table>

![](./Images/Img1.232.Ex5.GenerateWorkspaceDialog.png)

Click OK to accept the parameters. When prompted which tables to use from the source data (there are several) deselect all tables except for FoodVendors and click OK to create the workspace.

![](./Images/Img1.233.Ex5.SelectFTDialog.png)


<br>**2) Connect Reader/Writer**
<br>When first created, the reader and writer are not connected in this workspace. Connect them by dragging a connection from the output port of the reader feature type to the input port of the writer feature type labelled WayPoint:

![](./Images/Img1.234.Ex5.JoinFeatureTypes.png)

Click the expand buttons on the two objects to expose the list of attributes on each:

![](./Images/Img1.235.Ex5.ExposeAttributes.png)

Now drag a connection between the Reader attribute *VendorName* and the writer attribute *name*. Repeat the process for *VendorDescription* and *description*:

![](./Images/Img1.236.Ex5.JoinAttributes.png)

The technique of connecting objects like this is called Schema Mapping, and we shall learn more about it later.


<br>**3) Run Workspace**
<br>Save the workspace so you have a copy of it, then run the workspace by pressing the green run button. The workspace runs and the data is written to a Garmin POI dataset:

![](./Images/Img1.237.Ex5.LogWindow.png)


<br>**4) Inspect Data**
<br>Go to the FME Data Inspector. Select File &gt; Open Dataset from the menubar. This opens the dialog titled "Select Dataset to View". 

Set the format type and select the GPX dataset. However, the GPX format does not record its coordinate system inside the dataset, so to include a background map you must also set the coordinate system (LL83) in this dialog.

![](./Images/Img1.238.Ex5.DISetCoordSys.png)

***NB:*** *Because of the coordinate system limitation for this format, you can't use the Inspect options inside Workbench. That's because the data will be passed directly to the Data Inspector without the option to set the coordinate system. You have to open it manually as above.*

Click OK and the dataset will be opened for you to verify that it is correct.


<!--<br>**5) Filter Data**
<br>All this talk of food is making you hungry. It must be lunchtime. To find somewhere to get a quick lunch filter the data to show hot dog vendors in the city:

![](./Images/Img1.239.Ex5.FilterHotDogsInDataInspector.png)--> 


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
By completing this exercise you proved you know how to:
<br>
<ul><li>Create and run a workspace in FME Workbench</li>
<li>Carry out basic 'schema mapping' in FME Workbench</li>
<li>Open a dataset in the FME Data Inspector</li>
<!--<li>Filter data using test clauses in the FME Data Inspector</li>--> </ul>
</span>
</td>
</tr>
</table>


